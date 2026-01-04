from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_
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

import asyncio

# --- 接口实现 ---

@router.post("/sync")
async def sync_media(db: AsyncSession = Depends(get_db)):
    """同步 Emby 媒体数据，支持 10 并发并行拉取"""
    start_time = time.time()
    service = await get_emby_context(db)
    logger.info("🚀 [同步] 启动高并发同步引擎 (Concurrency: 10)...")
    
    unique_items = {} 
    item_to_series_tmdb = {}

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

    # 1. 抓取 Movie 和 Series
    top_items = await fetch_paged(["Movie", "Series"])
    for i in top_items:
        unique_items[i["Id"]] = i
        if i.get("Type") == "Series":
            tmdb = i.get("ProviderIds", {}).get("Tmdb")
            if tmdb: item_to_series_tmdb[i["Id"]] = tmdb
    
    # 2. 并行处理剧集子项
    series_items = [i for i in top_items if i.get("Type") == "Series"]
    total_series = len(series_items)
    logger.info(f"┣ 📂 准备并发处理 {total_series} 个剧集的子项...")

    # 信号量控制并发数
    sem = asyncio.Semaphore(10)
    processed_count = 0

    async def process_single_series(s_item):
        nonlocal processed_count
        async with sem:
            s_tmdb = item_to_series_tmdb.get(s_item["Id"])
            children = await fetch_paged(["Season", "Episode"], p_id=s_item["Id"])
            for child in children:
                # 继承逻辑
                if s_tmdb and not child.get("ProviderIds", {}).get("Tmdb"):
                    if "ProviderIds" not in child: child["ProviderIds"] = {}
                    child["ProviderIds"]["Tmdb"] = s_tmdb
                unique_items[child["Id"]] = child
            
            processed_count += 1
            if processed_count % 20 == 0 or processed_count == total_series:
                logger.info(f"┃  🕒 同步进度: {processed_count}/{total_series}...")

    # 启动并行任务
    tasks = [process_single_series(s) for s in series_items]
    await asyncio.gather(*tasks)
    
    # 3. 入库操作
    logger.info(f"┣ 💾 正在将 {len(unique_items)} 条数据存入本地库...")
    await db.execute(delete(MediaItem))
    
    for item_id, item in unique_items.items():
        v = next((s for s in item.get("MediaStreams", []) if s.get("Type") == "Video"), {})
        a = next((s for s in item.get("MediaStreams", []) if s.get("Type") == "Audio"), {})
        
        s_num = item.get("ParentIndexNumber") if item.get("Type") == "Episode" else item.get("IndexNumber") if item.get("Type") == "Season" else None
        e_num = item.get("IndexNumber") if item.get("Type") == "Episode" else None
        p_id = item.get("SeasonId") or item.get("SeriesId") or item.get("ParentId")
        
        db.add(MediaItem(
            id=item["Id"], name=item.get("Name"), item_type=item.get("Type"),
            tmdb_id=item.get("ProviderIds", {}).get("Tmdb"), path=item.get("Path"),
            year=item.get("ProductionYear"), parent_id=p_id,
            season_num=s_num, episode_num=e_num,
            display_title=v.get("DisplayTitle", "N/A"), video_codec=v.get("Codec", "N/A"),
            video_range=v.get("VideoRange", "N/A"), audio_codec=a.get("Codec", "N/A"),
            raw_data=item
        ))
    
    await db.commit()
    audit_log("高并发同步完成", (time.time()-start_time)*1000, [f"同步条数: {len(unique_items)}"])
    logger.info(f"✅ [同步] 成功，总计耗时: {int(time.time()-start_time)}s")
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
    """获取所有重复的电影、剧集本体、单集"""
    body_sub = select(MediaItem.tmdb_id).where(MediaItem.item_type.in_(["Movie", "Series"])).where(MediaItem.tmdb_id.isnot(None)).group_by(MediaItem.tmdb_id).having(func.count(MediaItem.id) > 1).subquery()
    bodies = await db.execute(select(MediaItem).where(MediaItem.tmdb_id.in_(select(body_sub))).where(MediaItem.item_type.in_(["Movie", "Series"])))
    
    ep_sub = select(MediaItem.tmdb_id, MediaItem.season_num, MediaItem.episode_num).where(MediaItem.item_type == "Episode").where(MediaItem.tmdb_id.isnot(None)).group_by(MediaItem.tmdb_id, MediaItem.season_num, MediaItem.episode_num).having(func.count(MediaItem.id) > 1).subquery()
    eps = await db.execute(select(MediaItem).join(ep_sub, (MediaItem.tmdb_id == ep_sub.c.tmdb_id) & (MediaItem.season_num == ep_sub.c.season_num) & (MediaItem.episode_num == ep_sub.c.episode_num)))
    
    res = []
    for item in list(bodies.scalars().all()) + list(eps.scalars().all()):
        res.append({"id": item.id, "name": item.name, "item_type": item.item_type, "path": item.path, "display_title": item.display_title, "video_codec": item.video_codec, "video_range": item.video_range, "tmdb_id": item.tmdb_id, "raw_data": item.raw_data, "is_duplicate": True})
    return res

@router.post("/smart-select")
async def smart_select_v4(db: AsyncSession = Depends(get_db)):
    """智能分析，支持区分命名空间"""
    config = get_config()
    rule_data = config.get("dedupe_rules")
    exclude_paths = config.get("exclude_paths", [])
    scorer = Scorer(rule_data)
    
    all_items_res = await db.execute(select(MediaItem).where(MediaItem.item_type.in_(["Movie", "Series", "Episode"])))
    all_items = all_items_res.scalars().all()
    
    groups = defaultdict(list)
    for i in all_items:
        if not i.tmdb_id: continue
        if i.item_type == "Movie": key = f"Movie-{i.tmdb_id}"
        elif i.item_type == "Series": key = f"Series-{i.tmdb_id}"
        elif i.item_type == "Episode": key = f"TV-{i.tmdb_id}-S{str(i.season_num or 0).zfill(2)}E{str(i.episode_num or 0).zfill(2)}"
        else: continue
        groups[key].append(i)
        
    to_delete_ids = []
    for key, g_items in groups.items():
        if len(g_items) > 1:
            scored_data = [{"id": i.id, "emby_id": i.id, "path": i.path, "display_title": i.display_title, "video_codec": i.video_codec, "video_range": i.video_range} for i in g_items]
            suggested = scorer.select_best(scored_data)
            for eid in suggested:
                item_obj = next(it for it in g_items if it.id == eid)
                if not any(item_obj.path.startswith(ex) for ex in exclude_paths if ex.strip()):
                    to_delete_ids.append(eid)
    
    if not to_delete_ids: return []
    final_res = await db.execute(select(MediaItem).where(MediaItem.id.in_(to_delete_ids)))
    return final_res.scalars().all()

@router.delete("/items")
async def delete_items_optimized(request: BulkDeleteRequest, db: AsyncSession = Depends(get_db)):
    """优化版删除：如果父节点也要被删除，则跳过子节点的 API 调用"""
    start_time = time.time()
    service = await get_emby_context(db)
    
    # 1. 预先获取所有待删除项目的层级信息
    res = await db.execute(select(MediaItem).where(MediaItem.id.in_(request.item_ids)))
    delete_map = {item.id: item for item in res.scalars().all()}
    
    # 2. 识别并折叠冗余操作
    final_ids_to_call = []
    skipped_count = 0
    
    for eid in request.item_ids:
        item = delete_map.get(eid)
        if not item: continue
        
        # 向上溯源：检查父级或更高级祖先是否也在删除列表中
        is_redundant = False
        current_p_id = item.parent_id
        while current_p_id:
            if current_p_id in request.item_ids:
                is_redundant = True
                break
            # 这里的简单实现假设 parent_id 已经在 MediaItem 里了，
            # 如果是跨层级（如 Series 直接删 Episode），需要数据库二次辅助
            # 但在我们的查重逻辑中，parent_id 已经覆盖了核心层级。
            # 这里我们通过查询确保准确
            p_res = await db.execute(select(MediaItem.parent_id).where(MediaItem.id == current_p_id))
            current_p_id = p_res.scalar()
            
        if is_redundant:
            logger.info(f"⚡ [优化] 跳过单集 API 调用 (父级已在清理列表): {item.path}")
            skipped_count += 1
        else:
            final_ids_to_call.append(eid)

    # 3. 执行物理删除
    success = 0
    for eid in final_ids_to_call:
        item = delete_map.get(eid)
        logger.warning(f"🔥 [清理] 执行 Emby 删除: {item.path if item else eid}")
        if await service.delete_item(eid):
            success += 1
            # 注意：即便 API 没调（被折叠了），数据库里的记录也要删掉
            # 这里统一处理
    
    # 4. 从本地库清理所有传入的 ID (包含被折叠的子项)
    await db.execute(delete(MediaItem).where(MediaItem.id.in_(request.item_ids)))
    await db.commit()
    
    audit_log("媒体清理任务执行完毕", (time.time()-start_time)*1000, [
        f"API 调用数: {len(final_ids_to_call)}",
        f"自动折叠子项数: {skipped_count}",
        f"成功数: {success}"
    ])
    return {"success": success, "skipped": skipped_count}

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
