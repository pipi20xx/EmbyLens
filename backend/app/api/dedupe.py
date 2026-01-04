from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.models.media import MediaItem, DedupeRule
from app.services.emby import EmbyService
from app.core.scorer import Scorer
from app.utils.logger import logger
import json
import re

router = APIRouter()

# --- 辅助：复刻原版解析逻辑 ---
SEARCH_FIELD_MAP = { "名称": "name", "路径": "path", "年份": "year", "embyid": "id", "tmdb": "tmdb_id" }

def parse_advanced_search(text: str):
    criteria = {}
    pattern = re.compile(r'(\w+):(?:"([^"]*)"|(\S+))')
    for match in pattern.finditer(text):
        field, quoted_value, unquoted_value = match.groups()
        field_key = field.lower()
        val = (quoted_value if quoted_value is not None else unquoted_value).strip()
        db_field = SEARCH_FIELD_MAP.get(field_key) or SEARCH_FIELD_MAP.get(field)
        if db_field:
            criteria[db_field] = val
    return criteria

# --- 请求模型 ---

class SyncRequest(BaseModel):
    item_types: List[str] = ["Movie", "Series"]

class SmartSelectRequest(BaseModel):
    rule_id: Optional[int] = None
    items: List[Dict[str, Any]]

class BulkDeleteRequest(BaseModel):
    item_ids: List[str]

class RuleCreate(BaseModel):
    name: str
    priority_order: List[str]
    values_weight: Dict[str, List[str]]
    tie_breaker: str = "small_id"
    is_default: bool = False

from app.core.config_manager import get_config
import re

# --- 工具函数 ---

async def get_emby_context(db: AsyncSession):
    config = get_config()
    url = config.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="未配置 Emby 服务器")
    
    # 优先使用 Session Token
    token = config.get("session_token") or config.get("api_key")
    return EmbyService(url, token, config.get("user_id"), config.get("tmdb_api_key"))


# --- 接口实现 ---

@router.post("/sync")
async def sync_media(request: SyncRequest = SyncRequest(), db: AsyncSession = Depends(get_db)):
    """同步 Emby 媒体到本地数据库以供查重 (独立的分页获取实现)"""
    service = await get_emby_context(db)
    logger.info(f"开始同步 Emby 媒体库 (全量模式): {request.item_types}")
    
    # 使用字典存储，确保 ID 唯一
    unique_items = {}
    
    # 内部实现分页获取，不修改 emby.py
    async def fetch_paged(types, p_id=None):
        fetched = []
        limit = 300
        start = 0
        while True:
            params = {
                "IncludeItemTypes": ",".join(types),
                "Recursive": "true",
                "Fields": "Path,ProductionYear,ProviderIds,MediaStreams,DisplayTitle,SortName,ParentId,SeriesId,SeasonId,IndexNumber,ParentIndexNumber,RunTimeTicks",
                "StartIndex": start,
                "Limit": limit
            }
            if p_id: 
                params["ParentId"] = p_id
                # 如果指定了父 ID 且是获取季/集，就不再需要全局递归
                params["Recursive"] = "true"
                
            resp = await service._request("GET", "/Items", params=params)
            if not resp or resp.status_code != 200: break
            batch = resp.json().get("Items", [])
            if not batch: break
            fetched.extend(batch)
            if len(batch) < limit: break
            start += limit
        return fetched

    # 1. 获取顶级项目 (Movie 和 Series)
    top_items = await fetch_paged(request.item_types)
    for item in top_items:
        unique_items[item["Id"]] = item
    
    # 2. 如果包含 Series，递归获取下级所有季和集
    if "Series" in request.item_types:
        series_items = [i for i in top_items if i.get("Type") == "Series"]
        logger.info(f"正在同步 {len(series_items)} 个剧集的子项...")
        for s_item in series_items:
            # 这里的 fetch_paged 会拿到该剧集下的所有 Season 和 Episode
            children = await fetch_paged(["Season", "Episode"], p_id=s_item["Id"])
            for child in children:
                unique_items[child["Id"]] = child
    
    # 3. 持久化到本地数据库
    await db.execute(delete(MediaItem))
    
    count = 0
    for item_id, item in unique_items.items():
        streams = item.get("MediaStreams", [])
        v_stream = next((s for s in streams if s.get("Type") == "Video"), {})
        a_stream = next((s for s in streams if s.get("Type") == "Audio"), {})
        
        # 处理父级 ID
        # 对于集，优先关联季 ID；对于季，关联剧集 ID
        p_id = item.get("SeasonId") or item.get("SeriesId") or item.get("ParentId")
        
        media_item = MediaItem(
            id=item["Id"],
            name=item.get("Name"),
            item_type=item.get("Type"),
            tmdb_id=item.get("ProviderIds", {}).get("Tmdb"),
            path=item.get("Path"),
            year=item.get("ProductionYear"),
            parent_id=p_id,
            season_num=item.get("ParentIndexNumber") if item.get("Type") == "Episode" else item.get("IndexNumber") if item.get("Type") == "Season" else None,
            episode_num=item.get("IndexNumber") if item.get("Type") == "Episode" else None,
            display_title=v_stream.get("DisplayTitle", "N/A"),
            video_codec=v_stream.get("Codec", "N/A"),
            video_range=v_stream.get("VideoRange", "N/A"),
            audio_codec=a_stream.get("Codec", "N/A"),
            raw_data=item
        )
        db.add(media_item)
        count += 1
        
    await db.commit()
    logger.info(f"✅ 同步完成，共存入 {count} 条数据")
    return {"message": "同步成功", "count": count}

@router.get("/items")
async def get_all_items(
    query_text: Optional[str] = None,
    item_type: Optional[str] = None,
    parent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取所有媒体项目，1:1 复刻原版的高级搜索逻辑"""
    query = select(MediaItem)
    
    if query_text:
        if ":" in query_text:
            criteria = parse_advanced_search(query_text)
            for field, value in criteria.items():
                if field == "year":
                    try: query = query.where(MediaItem.year == int(value))
                    except: pass
                else:
                    query = query.where(getattr(MediaItem, field).ilike(f"%{value}%"))
        else:
            # 普通模糊匹配
            query = query.where(
                (MediaItem.name.ilike(f"%{query_text}%")) |
                (MediaItem.path.ilike(f"%{query_text}%")) |
                (MediaItem.id == query_text)
            )
    
    # 基础过滤逻辑
    if parent_id:
        query = query.where(MediaItem.parent_id == parent_id)
    elif not query_text:
        # 如果没有搜索文本，默认只显示 Movie 和 Series
        if item_type:
            query = query.where(MediaItem.item_type == item_type)
        else:
            query = query.where(MediaItem.item_type.in_(["Movie", "Series"]))
            
    query = query.order_by(MediaItem.name)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/duplicates")
async def list_duplicates(db: AsyncSession = Depends(get_db)):
    """查找 TMDB ID 重复的项目 (电影) 以及 编号重复的项目 (单集)"""
    
    # 1. 查找重复电影 (按 TMDBID)
    movie_sub = (
        select(MediaItem.tmdb_id)
        .where(MediaItem.item_type == "Movie")
        .where(MediaItem.tmdb_id.isnot(None))
        .group_by(MediaItem.tmdb_id)
        .having(func.count(MediaItem.id) > 1)
        .subquery()
    )
    movies = await db.execute(select(MediaItem).where(MediaItem.tmdb_id.in_(select(movie_sub))))
    
    # 2. 查找重复单集 (按 SeriesTMDB + 季 + 集)
    # 注意：这里的 tmdb_id 通常是剧集的 ID
    ep_sub = (
        select(MediaItem.tmdb_id, MediaItem.season_num, MediaItem.episode_num)
        .where(MediaItem.item_type == "Episode")
        .where(MediaItem.tmdb_id.isnot(None))
        .group_by(MediaItem.tmdb_id, MediaItem.season_num, MediaItem.episode_num)
        .having(func.count(MediaItem.id) > 1)
        .subquery()
    )
    eps = await db.execute(
        select(MediaItem).join(
            ep_sub, 
            (MediaItem.tmdb_id == ep_sub.c.tmdb_id) & 
            (MediaItem.season_num == ep_sub.c.season_num) & 
            (MediaItem.episode_num == ep_sub.c.episode_num)
        )
    )
    
    all_items = list(movies.scalars().all()) + list(eps.scalars().all())
    
    # 分组逻辑
    groups = {}
    for item in all_items:
        key = item.tmdb_id
        if item.item_type == "Episode":
            key = f"{item.tmdb_id}-S{str(item.season_num).zfill(2)}E{str(item.episode_num).zfill(2)}"
            
        if key not in groups:
            groups[key] = []
        groups[key].append({
            "id": item.id,
            "name": item.name,
            "item_type": item.item_type, # 统一字段名
            "type": item.item_type,
            "path": item.path,
            "display_title": item.display_title,
            "video_codec": item.video_codec,
            "video_range": item.video_range,
            "audio_codec": item.audio_codec,
            "tmdb_id": item.tmdb_id,
            "raw_data": item.raw_data
        })
    
    return [{"tmdb_id": k, "items": v} for k, v in groups.items()]

@router.get("/config")
async def get_dedupe_config():
    config = get_config()
    return {
        "rules": config.get("dedupe_rules"),
        "exclude_paths": config.get("exclude_paths", [])
    }

@router.post("/config")
async def save_dedupe_config(data: Dict[str, Any]):
    config = get_config()
    if "rules" in data: config["dedupe_rules"] = data["rules"]
    if "exclude_paths" in data: config["exclude_paths"] = data["exclude_paths"]
    save_config(config)
    return {"message": "配置已更新"}

@router.post("/smart-select")
async def smart_select_items(request: SmartSelectRequest, db: AsyncSession = Depends(get_db)):
    """应用智能选中规则，并严格执行路径排除。支持电影和集的精准分组。"""
    config = get_config()
    rule_data = config.get("dedupe_rules")
    exclude_paths = config.get("exclude_paths", [])
        
    scorer = Scorer(rule_data)
    
    # --- 核心：精准分组逻辑 ---
    from collections import defaultdict
    groups = defaultdict(list)
    
    for item in request.items:
        tmdb_id = item.get("tmdb_id")
        if not tmdb_id or tmdb_id == "N/A":
            continue
            
        item_type = item.get("item_type") or item.get("type")
        group_key = tmdb_id
        
        # 如果是集，需要根据剧集TMDB+季+集生成唯一分组Key
        if item_type == "Episode":
            raw = item.get("raw_data") or {}
            s_num = raw.get("ParentIndexNumber")
            e_num = raw.get("IndexNumber")
            if s_num is not None and e_num is not None:
                # 组合键格式: TMDB-S01E01
                group_key = f"{tmdb_id}-S{str(s_num).zfill(2)}E{str(e_num).zfill(2)}"
            else:
                # 无法解析编号的集不参与自动去重
                continue
        
        groups[group_key].append(item)
        
    to_delete = []
    for g_key, group_items in groups.items():
        if len(group_items) > 1:
            # 执行评分排序逻辑 (Scorer 内部按分数从好到坏排序，返回建议删除的 ID 列表)
            # 传入的 item 必须包含 emby_id 字段供 Scorer 识别
            # 我们统一一下字段名，Scorer 期待的是 emby_id
            for i in group_items: i["emby_id"] = i["id"]
            
            suggested = scorer.select_best(group_items)
            
            # --- 路径排除过滤 ---
            filtered_suggested = []
            for eid in suggested:
                item_obj = next((i for i in group_items if i["id"] == eid), None)
                if not item_obj: continue
                
                path = item_obj.get("path", "")
                is_excluded = any(path.startswith(ex) for ex in exclude_paths if ex.strip())
                
                if not is_excluded:
                    filtered_suggested.append(eid)
                else:
                    logger.info(f"🛡️ 路径排除已生效，保护项目: {path}")
            
            to_delete.extend(filtered_suggested)
            
    return {"to_delete": to_delete}

@router.delete("/items")
async def delete_items(request: BulkDeleteRequest, db: AsyncSession = Depends(get_db)):
    """批量删除 Emby 媒体文件"""
    service = await get_emby_context(db)
    success = 0
    for eid in request.item_ids:
        if await service.delete_item(eid):
            success += 1
            await db.execute(delete(MediaItem).where(MediaItem.id == eid))
    
    await db.commit()
    return {"message": "删除操作完成", "success": success, "total": len(request.item_ids)}

@router.get("/rules")
async def get_rules(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(DedupeRule))
    return res.scalars().all()

@router.post("/rules")
async def create_rule(rule: RuleCreate, db: AsyncSession = Depends(get_db)):
    new_rule = DedupeRule(**rule.dict())
    db.add(new_rule)
    await db.commit()
    return {"id": new_rule.id, "message": "规则已创建"}
