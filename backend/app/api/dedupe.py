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
async def sync_media(request: SyncRequest, db: AsyncSession = Depends(get_db)):
    """同步 Emby 媒体到本地数据库以供查重"""
    service = await get_emby_context(db)
    logger.info(f"开始增量同步 Emby 媒体库: {request.item_types}")
    
    # 1. 获取顶级项目
    top_items = await service.fetch_items(request.item_types)
    all_fetched = list(top_items)
    
    # 2. 递归获取 Series 的子项 (Season/Episode)
    if "Series" in request.item_types:
        for series in [i for i in top_items if i.get("Type") == "Series"]:
            seasons = await service.fetch_items(["Season"], parent_id=series["Id"])
            all_fetched.extend(seasons)
            for season in seasons:
                episodes = await service.fetch_items(["Episode"], parent_id=season["Id"])
                all_fetched.extend(episodes)
    
    # 3. 清空并重新填充 (简单处理)
    await db.execute(delete(MediaItem))
    
    count = 0
    for item in all_fetched:
        # 提取流信息
        streams = item.get("MediaStreams", [])
        v_stream = next((s for s in streams if s.get("Type") == "Video"), {})
        a_stream = next((s for s in streams if s.get("Type") == "Audio"), {})
        
        media_item = MediaItem(
            id=item["Id"],
            name=item.get("Name"),
            item_type=item.get("Type"),
            tmdb_id=item.get("ProviderIds", {}).get("Tmdb"),
            path=item.get("Path"),
            year=item.get("ProductionYear"),
            parent_id=item.get("ParentId") or item.get("SeriesId") or item.get("SeasonId"),
            display_title=v_stream.get("DisplayTitle", "N/A"),
            video_codec=v_stream.get("Codec", "N/A"),
            video_range=v_stream.get("VideoRange", "N/A"),
            audio_codec=a_stream.get("Codec", "N/A"),
            raw_data=item
        )
        db.add(media_item)
        count += 1
        
    await db.commit()
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
    """查找 TMDB ID 重复的项目"""
    # 查找有多个 ID 对应同一个 TMDB ID 的组
    subquery = (
        select(MediaItem.tmdb_id)
        .where(MediaItem.item_type.in_(["Movie", "Series"]))
        .where(MediaItem.tmdb_id.isnot(None))
        .group_by(MediaItem.tmdb_id)
        .having(func.count(MediaItem.id) > 1)
        .subquery()
    )
    
    query = select(MediaItem).where(MediaItem.tmdb_id.in_(select(subquery)))
    result = await db.execute(query)
    items = result.scalars().all()
    
    groups = {}
    for item in items:
        if item.tmdb_id not in groups:
            groups[item.tmdb_id] = []
        groups[item.tmdb_id].append({
            "emby_id": item.id,
            "name": item.name,
            "type": item.item_type,
            "path": item.path,
            "display_title": item.display_title,
            "video_codec": item.video_codec,
            "video_range": item.video_range,
            "audio_codec": item.audio_codec,
            "tmdb_id": item.tmdb_id
        })
    
    return [{"tmdb_id": k, "items": v} for k, v in groups.items()]

@router.post("/smart-select")
async def smart_select_items(request: SmartSelectRequest, db: AsyncSession = Depends(get_db)):
    """应用智能选中规则，返回建议删除的 ID 列表"""
    if request.rule_id:
        res = await db.execute(select(DedupeRule).where(DedupeRule.id == request.rule_id))
        rule = res.scalars().first()
    else:
        res = await db.execute(select(DedupeRule).where(DedupeRule.is_default == True))
        rule = res.scalars().first()
        
    if not rule:
        # 硬编码默认规则
        rule_data = {
            "priority_order": ["display_title", "video_codec", "video_range"],
            "values_weight": {
                "display_title": ["4k", "2160p", "1080p", "720p"],
                "video_codec": ["hevc", "h264", "av1"],
                "video_range": ["hdr", "dolbyvision", "sdr"]
            },
            "tie_breaker": "small_id"
        }
    else:
        rule_data = {
            "priority_order": rule.priority_order,
            "values_weight": rule.values_weight,
            "tie_breaker": rule.tie_breaker
        }
        
    scorer = Scorer(rule_data)
    
    # 按照 TMDB ID 分组处理
    from collections import defaultdict
    groups = defaultdict(list)
    for item in request.items:
        groups[item.get("tmdb_id")].append(item)
        
    to_delete = []
    for tmdb_id, group_items in groups.items():
        if len(group_items) > 1:
            suggested = scorer.select_best(group_items)
            to_delete.extend(suggested)
            
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
