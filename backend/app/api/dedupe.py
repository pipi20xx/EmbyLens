from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.models.media import MediaItem
from app.services.emby import EmbyService
from app.core.scorer import Scorer
from app.core.config_manager import get_config, save_config
from app.utils.logger import logger, audit_log
import time
import re
from collections import defaultdict

router = APIRouter()

# --- 辅助逻辑 ---
SEARCH_FIELD_MAP = { "名称": "name", "路径": "path", "年份": "year", "embyid": "id", "tmdb": "tmdb_id" }

def parse_advanced_search(text: str):
    criteria = {}
    pattern = re.compile(r'(\w+):(?:"([^"]*)"|(\S+))')
    for match in pattern.finditer(text):
        field, quoted_value, unquoted_value = match.groups()
        field_key = field.lower()
        val = (quoted_value if quoted_value is not None else unquoted_value).strip()
        db_field = SEARCH_FIELD_MAP.get(field_key) or SEARCH_FIELD_MAP.get(field)
        if db_field: criteria[db_field] = val
    return criteria

async def get_emby_context(db: AsyncSession):
    config = get_config()
    url = config.get("url")
    if not url: raise HTTPException(status_code=400, detail="未配置 Emby 服务器")
    token = config.get("session_token") or config.get("api_key")
    return EmbyService(url, token, config.get("user_id"), config.get("tmdb_api_key"))

class BulkDeleteRequest(BaseModel):
    item_ids: List[str]

# --- 接口实现 ---

@router.post("/sync")
async def sync_media(db: AsyncSession = Depends(get_db)):
    """同步 Emby 媒体，包含 TMDB ID 继承逻辑"""
    start_time = time.time()
    service = await get_emby_context(db)
    logger.info("🚀 [同步] 开始全量拉取数据...")
    
    unique_items = {} # id -> item_data
    item_to_series_tmdb = {} # item_id -> series_tmdb_id (用于继承)

    async def fetch_paged(types, p_id=None):
        fetched = []
        limit = 300
        start = 0
        while True:
            params = {
                "IncludeItemTypes": ",".join(types), "Recursive": "true",
                "Fields": "Path,ProductionYear,ProviderIds,MediaStreams,DisplayTitle,SortName,ParentId,SeriesId,SeasonId,IndexNumber,ParentIndexNumber",
                "StartIndex": start, "Limit": limit
            }
            if p_id: params["ParentId"] = p_id
            resp = await service._request("GET", "/Items", params=params)
            if not resp or resp.status_code != 200: break
            batch = resp.json().get("Items", [])
            if not batch: break
            fetched.extend(batch)
            if len(batch) < limit: break
            start += limit
        return fetched

    # 1. 获取顶级项目
    top_items = await fetch_paged(["Movie", "Series"])
    for i in top_items:
        unique_items[i["Id"]] = i
        if i.get("Type") == "Series":
            s_tmdb = i.get("ProviderIds", {}).get("Tmdb")
            if s_tmdb: item_to_series_tmdb[i["Id"]] = s_tmdb
    
    # 2. 获取剧集子项并继承 TMDB ID
    series_items = [i for i in top_items if i.get("Type") == "Series"]
    logger.info(f"┣ 📂 正在解析 {len(series_items)} 个剧集的单集信息...")
    for s_item in series_items:
        s_tmdb = item_to_series_tmdb.get(s_item["Id"])
        children = await fetch_paged(["Season", "Episode"], p_id=s_item["Id"])
        for child in children:
            # 关键：如果单集没有 TMDB，强制继承剧集的 TMDB
            if s_tmdb and not child.get("ProviderIds", {}).get("Tmdb"):
                if "ProviderIds" not in child: child["ProviderIds"] = {}
                child["ProviderIds"]["Tmdb"] = s_tmdb
            unique_items[child["Id"]] = child
    
    # 3. 持久化
    await db.execute(delete(MediaItem))
    for item_id, item in unique_items.items():
        v = next((s for s in item.get("MediaStreams", []) if s.get("Type") == "Video"), {})
        a = next((s for s in item.get("MediaStreams", []) if s.get("Type") == "Audio"), {})
        
        db.add(MediaItem(
            id=item["Id"], name=item.get("Name"), item_type=item.get("Type"),
            tmdb_id=item.get("ProviderIds", {}).get("Tmdb"), path=item.get("Path"),
            year=item.get("ProductionYear"), 
            parent_id=item.get("SeasonId") or item.get("SeriesId") or item.get("ParentId"),
            season_num=item.get("ParentIndexNumber") if item.get("Type") == "Episode" else item.get("IndexNumber") if item.get("Type") == "Season" else None,
            episode_num=item.get("IndexNumber") if item.get("Type") == "Episode" else None,
            display_title=v.get("DisplayTitle", "N/A"), video_codec=v.get("Codec", "N/A"),
            video_range=v.get("VideoRange", "N/A"), audio_codec=a.get("Codec", "N/A"),
            raw_data=item
        ))
    
    await db.commit()
    logger.info(f"✅ [同步] 成功存入 {len(unique_items)} 条数据")
    return {"message": "ok"}

@router.get("/items")
async def get_all_items(query_text: Optional[str] = None, item_type: Optional[str] = None, parent_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(MediaItem)
    if query_text:
        if ":" in query_text:
            for f, v in parse_advanced_search(query_text).items():
                if f == "year":
                    try: query = query.where(MediaItem.year == int(v))
                    except: pass
                else: query = query.where(getattr(MediaItem, f).ilike(f"%{v}%"))
        else: query = query.where((MediaItem.name.ilike(f"%{query_text}%")) | (MediaItem.path.ilike(f"%{query_text}%")) | (MediaItem.id == query_text))
    if parent_id: query = query.where(MediaItem.parent_id == parent_id)
    elif not query_text:
        if item_type: query = query.where(MediaItem.item_type == item_type)
        else: query = query.where(MediaItem.item_type.in_(["Movie", "Series"]))
    result = await db.execute(query.order_by(MediaItem.name))
    return result.scalars().all()

@router.get("/duplicates")
async def list_duplicates(db: AsyncSession = Depends(get_db)):
    """查重模式：列出所有处于重复状态的节点"""
    # 同步逻辑中的 ID 继承已经保证了单集有 tmdb_id
    body_sub = select(MediaItem.tmdb_id).where(MediaItem.item_type.in_(["Movie", "Series"])).where(MediaItem.tmdb_id.isnot(None)).group_by(MediaItem.tmdb_id).having(func.count(MediaItem.id) > 1).subquery()
    ep_sub = select(MediaItem.tmdb_id, MediaItem.season_num, MediaItem.episode_num).where(MediaItem.item_type == "Episode").where(MediaItem.tmdb_id.isnot(None)).group_by(MediaItem.tmdb_id, MediaItem.season_num, MediaItem.episode_num).having(func.count(MediaItem.id) > 1).subquery()
    
    bodies = await db.execute(select(MediaItem).where(MediaItem.tmdb_id.in_(select(body_sub))))
    eps = await db.execute(select(MediaItem).join(ep_sub, (MediaItem.tmdb_id == ep_sub.c.tmdb_id) & (MediaItem.season_num == ep_sub.c.season_num) & (MediaItem.episode_num == ep_sub.c.episode_num)))
    
    res = []
    for item in list(bodies.scalars().all()) + list(eps.scalars().all()):
        res.append({"id": item.id, "name": item.name, "item_type": item.item_type, "path": item.path, "display_title": item.display_title, "video_codec": item.video_codec, "video_range": item.video_range, "tmdb_id": item.tmdb_id, "raw_data": item.raw_data, "is_duplicate": True})
    return res

@router.post("/smart-select")
async def smart_select_v3(db: AsyncSession = Depends(get_db)):
    """核心：智能评分并输出详尽比对日志"""
    config = get_config()
    rule_data = config.get("dedupe_rules")
    exclude_paths = config.get("exclude_paths", [])
    scorer = Scorer(rule_data)
    
    logger.info("🧪 [智能分析] 评分引擎启动...")
    
    all_items_res = await db.execute(select(MediaItem).where(MediaItem.item_type.in_(["Movie", "Series", "Episode"])))
    all_items = all_items_res.scalars().all()
    
    groups = defaultdict(list)
    for i in all_items:
        if not i.tmdb_id: continue
        key = i.tmdb_id
        if i.item_type == "Episode":
            # 组合键确保不同剧集下的同一集能被比对
            key = f"{i.tmdb_id}-S{str(i.season_num or 0).zfill(2)}E{str(i.episode_num or 0).zfill(2)}"
        groups[key].append(i)
        
    to_delete_ids = []
    for key, g_items in groups.items():
        if len(g_items) > 1:
            scored_data = [{"id": i.id, "emby_id": i.id, "path": i.path, "display_title": i.display_title, "video_codec": i.video_codec, "video_range": i.video_range} for i in g_items]
            suggested = scorer.select_best(scored_data)
            
            logger.info(f"┃  ┣ 📦 发现重复组 [{key}]，包含 {len(g_items)} 个节点")
            for i in g_items:
                is_to_del = i.id in suggested
                status = "🗑️ 建议删除" if is_to_del else "✅ 建议保留"
                
                # 白名单二次校验
                if is_to_del and any(i.path.startswith(ex) for ex in exclude_paths if ex.strip()):
                    status = "🛡️ 路径保护"
                    suggested.remove(i.id)
                
                logger.info(f"┃  ┃  ┗ {status}: [{i.display_title} | {i.video_codec}] {i.path}")
            
            to_delete_ids.extend(suggested)
    
    if not to_delete_ids: return []
    final_res = await db.execute(select(MediaItem).where(MediaItem.id.in_(to_delete_ids)))
    return final_res.scalars().all()

@router.delete("/items")
async def delete_items(request: BulkDeleteRequest, db: AsyncSession = Depends(get_db)):
    service = await get_emby_context(db)
    success = 0
    for eid in request.item_ids:
        item_res = await db.execute(select(MediaItem).where(MediaItem.id == eid))
        item = item_res.scalars().first()
        if item:
            logger.warning(f"🔥 [清理] 正在物理删除: {item.path}")
            if await service.delete_item(eid):
                success += 1
                await db.execute(delete(MediaItem).where(MediaItem.id == eid))
    await db.commit()
    return {"success": success}

@router.get("/config")
async def get_dedupe_config():
    config = get_config()
    return {"rules": config.get("dedupe_rules"), "exclude_paths": config.get("exclude_paths", [])}

@router.post("/config")
async def save_dedupe_config(data: Dict[str, Any]):
    config = get_config()
    if "rules" in data: config["dedupe_rules"] = data["rules"]
    if "exclude_paths" in data: config["exclude_paths"] = data["exclude_paths"]
    save_config(config)
    return {"message": "ok"}
