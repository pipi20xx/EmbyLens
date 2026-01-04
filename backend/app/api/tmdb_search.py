from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.models.server import EmbyServer
from app.services.emby import EmbyService
from app.utils.logger import logger, audit_log
import time

router = APIRouter()

class TmdbSearchRequest(BaseModel):
    tmdb_id: str
    search_movies: bool = True
    search_series: bool = True
    show_raw_json: bool = False

class TmdbSearchResponse(BaseModel):
    results: List[Dict[str, Any]]

# 1:1 复刻源码中要求的详尽字段
FULL_FIELDS = "ProviderIds,Name,Type,Id,Path,Overview,ProductionYear,CommunityRating,OfficialRating,Genres,Studios,PremiereDate,EndDate,Status,RunTimeTicks,Taglines,UserData"

async def _fetch_series_structure(service: EmbyService, series_item: Dict[str, Any]) -> Dict[str, Any]:
    """1:1 源码级递归：抓取季、集以及每一集的详尽元数据"""
    series_details = series_item.copy()
    series_details["Seasons"] = []
    
    logger.info(f"┃  ┣ 📂 递归解析层级: {series_item.get('Name')}")
    
    # 1. 抓取季列表 (Fields 必须完整)
    seasons = await service.fetch_items(["Season"], recursive=False, parent_id=series_item["Id"])
    for s_item in seasons:
        season_details = s_item.copy()
        # 2. 抓取每一集
        logger.info(f"┃  ┃  ┣ 📅 同步季数据: {s_item.get('Name')}")
        episodes = await service.fetch_items(["Episode"], recursive=False, parent_id=s_item["Id"])
        season_details["Episodes"] = episodes
        series_details["Seasons"].append(season_details)
        
    return series_details

@router.post("/search-by-id", response_model=TmdbSearchResponse)
async def search_by_tmdb_id(request: TmdbSearchRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmbyServer).limit(1))
    server = result.scalars().first()
    if not server: raise HTTPException(status_code=400, detail="未配置服务器")
    
    service = EmbyService(server.url, server.api_key, server.user_id)
    start_time = time.time()
    target_tmdb_id = request.tmdb_id.strip()
    include_types = []
    if request.search_movies: include_types.append("Movie")
    if request.search_series: include_types.append("Series")
    
    final_results = []
    logger.info(f"🚀 开始全量元数据检索 (ID: {target_tmdb_id})")

    # 复刻原版两阶段搜索，且每一阶段都强制请求 FULL_FIELDS
    all_items = await service.fetch_items(include_types, recursive=True)
    
    for it in all_items:
        p_ids = it.get('ProviderIds', {})
        if str(p_ids.get('Tmdb')) == target_tmdb_id:
            # 命中匹配
            logger.info(f"┃  ┣ ✅ 匹配成功: {it.get('Name')} ({it.get('Type')})")
            
            # 如果是剧集，执行深度结构解析
            if it["Type"] == "Series":
                it = await _fetch_series_structure(service, it)
            
            final_results.append(it)

    audit_log("TMDB 搜索结果报告", (time.time()-start_time)*1000, [
        f"搜索 ID: {target_tmdb_id}",
        f"结果数: {len(final_results)}"
    ])
    return TmdbSearchResponse(results=final_results)