from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.models.media import MediaItem, DedupeRule
from app.services.emby import EmbyService
from app.core.scorer import Scorer
from app.core.config_manager import get_config, save_config
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
    items: List[Dict[str, Any]]

class BulkDeleteRequest(BaseModel):
    item_ids: List[str]

# --- 工具函数 ---

async def get_emby_context(db: AsyncSession):
    config = get_config()
    url = config.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="未配置 Emby 服务器")
    token = config.get("session_token") or config.get("api_key")
    return EmbyService(url, token, config.get("user_id"), config.get("tmdb_api_key"))

# --- 接口实现 ---

@router.post("/sync")
async def sync_media(request: SyncRequest = SyncRequest(), db: AsyncSession = Depends(get_db)):
    service = await get_emby_context(db)
    unique_items = {}
    
    async def fetch_paged(types, p_id=None):
        fetched = []
        limit = 300
        start = 0
        while True:
            params = {
                "IncludeItemTypes": ",".join(types),
                "Recursive": "true",
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

    # 同步 Movie 和 Series
    top_items = await fetch_paged(request.item_types)
    for i in top_items: unique_items[i["Id"]] = i
    
    if "Series" in request.item_types:
        series_items = [i for i in top_items if i.get("Type") == "Series"]
        for s_item in series_items:
            children = await fetch_paged(["Season", "Episode"], p_id=s_item["Id"])
            for child in children: unique_items[child["Id"]] = child
    
    await db.execute(delete(MediaItem))
    count = 0
    for item_id, item in unique_items.items():
        streams = item.get("MediaStreams", [])
        v = next((s for s in streams if s.get("Type") == "Video"), {})
        a = next((s for s in streams if s.get("Type") == "Audio"), {})
        p_id = item.get("SeasonId") or item.get("SeriesId") or item.get("ParentId")
        
        db.add(MediaItem(
            id=item["Id"], name=item.get("Name"), item_type=item.get("Type"),
            tmdb_id=item.get("ProviderIds", {}).get("Tmdb"), path=item.get("Path"),
            year=item.get("ProductionYear"), parent_id=p_id,
            season_num=item.get("ParentIndexNumber") if item.get("Type") == "Episode" else item.get("IndexNumber") if item.get("Type") == "Season" else None,
            episode_num=item.get("IndexNumber") if item.get("Type") == "Episode" else None,
            display_title=v.get("DisplayTitle", "N/A"), video_codec=v.get("Codec", "N/A"),
            video_range=v.get("VideoRange", "N/A"), audio_codec=a.get("Codec", "N/A"),
            raw_data=item
        ))
        count += 1
    await db.commit()
    return {"message": "同步成功", "count": count}

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
    """核心：查找重复的电影、剧集本体以及重复的单集"""
    # 1. 重复电影/剧集本体 (按 TMDBID 分组)
    body_sub = select(MediaItem.tmdb_id).where(MediaItem.item_type.in_(["Movie", "Series"])).where(MediaItem.tmdb_id.isnot(None)).group_by(MediaItem.tmdb_id).having(func.count(MediaItem.id) > 1).subquery()
    bodies = await db.execute(select(MediaItem).where(MediaItem.tmdb_id.in_(select(body_sub))))
    
    # 2. 重复单集 (按 SeriesTMDB + 季号 + 集号 分组)
    ep_sub = select(MediaItem.tmdb_id, MediaItem.season_num, MediaItem.episode_num).where(MediaItem.item_type == "Episode").where(MediaItem.tmdb_id.isnot(None)).group_by(MediaItem.tmdb_id, MediaItem.season_num, MediaItem.episode_num).having(func.count(MediaItem.id) > 1).subquery()
    eps = await db.execute(select(MediaItem).join(ep_sub, (MediaItem.tmdb_id == ep_sub.c.tmdb_id) & (MediaItem.season_num == ep_sub.c.season_num) & (MediaItem.episode_num == ep_sub.c.episode_num)))
    
    all_items = list(bodies.scalars().all()) + list(eps.scalars().all())
    groups = {}
    for item in all_items:
        key = item.tmdb_id
        if item.item_type == "Episode":
            key = f"{item.tmdb_id}-S{str(item.season_num).zfill(2)}E{str(item.episode_num).zfill(2)}"
        if key not in groups: groups[key] = []
        groups[key].append({"id": item.id, "name": item.name, "item_type": item.item_type, "path": item.path, "display_title": item.display_title, "video_codec": item.video_codec, "video_range": item.video_range, "tmdb_id": item.tmdb_id, "raw_data": item.raw_data})
    return [{"tmdb_id": k, "items": v} for k, v in groups.items()]

@router.post("/smart-select")
async def smart_select_items(request: SmartSelectRequest, db: AsyncSession = Depends(get_db)):
    config = get_config()
    rule_data = config.get("dedupe_rules")
    if not rule_data:
        # 最后的兜底
        rule_data = {
            "priority_order": ["display_title", "video_codec", "video_range"],
            "values_weight": {"display_title": ["4k", "1080p"], "video_codec": ["hevc", "h264"], "video_range": ["hdr", "sdr"]},
            "tie_breaker": "small_id"
        }
    
    exclude_paths = config.get("exclude_paths", [])
    scorer = Scorer(rule_data)
    from collections import defaultdict
    groups = defaultdict(list)
    for item in request.items:
        tmdb_id = item.get("tmdb_id")
        if not tmdb_id: continue
        key = tmdb_id
        if item.get("item_type") == "Episode":
            raw = item.get("raw_data") or {}
            s, e = raw.get("ParentIndexNumber"), raw.get("IndexNumber")
            if s is not None and e is not None: key = f"{tmdb_id}-S{str(s).zfill(2)}E{str(e).zfill(2)}"
            else: continue
        groups[key].append(item)
    to_delete = []
    for g_items in groups.values():
        if len(g_items) > 1:
            for i in g_items: i["emby_id"] = i["id"] # Scorer 期待 emby_id
            suggested = scorer.select_best(g_items)
            for eid in suggested:
                item_obj = next((i for i in g_items if i["id"] == eid), None)
                if not item_obj: continue
                if not any(item_obj.get("path", "").startswith(ex) for ex in exclude_paths if ex.strip()):
                    to_delete.append(eid)
    return {"to_delete": to_delete}

@router.delete("/items")
async def delete_items(request: BulkDeleteRequest, db: AsyncSession = Depends(get_db)):
    service = await get_emby_context(db)
    success = 0
    for eid in request.item_ids:
        if await service.delete_item(eid):
            success += 1
            await db.execute(delete(MediaItem).where(MediaItem.id == eid))
    await db.commit()
    return {"message": "删除完成", "success": success, "total": len(request.item_ids)}

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
    return {"message": "配置更新"}