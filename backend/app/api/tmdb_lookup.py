from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.server import EmbyServer
from app.services.emby import EmbyService
from app.utils.logger import logger, audit_log
from sqlalchemy import select
import time

router = APIRouter()

@router.get("/reverse-tmdb", summary="根据单集 ID 反查剧集 TMDB")
async def reverse_lookup_tmdb(
    episode_id: str = Query(..., description="Emby 单集 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    1:1 源码复刻：单集 ID -> SeriesId -> TMDB ID
    """
    result = await db.execute(select(EmbyServer).limit(1))
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=400, detail="未配置服务器")

    start_time = time.time()
    service = EmbyService(server.url, server.api_key, server.user_id)
    
    logger.info(f"🔍 启动单集反向溯源: {episode_id}")
    
    # 步骤 1: 获取单集，拿到 SeriesId
    episode_data = await service.get_item(episode_id)
    if not episode_data:
        raise HTTPException(status_code=404, detail="单集未找到")
    
    series_id = episode_data.get('SeriesId')
    if not series_id:
        logger.error(f"┗ ❌ 识别失败: 该项目 ({episode_id}) 没有绑定的剧集 ID")
        raise HTTPException(status_code=400, detail="该 ID 不是剧集单集或没有上级剧集")

    # 步骤 2: 获取剧集，拿到 TMDB ID
    logger.info(f"┣ 🔗 已定位上级剧集 ID: {series_id}")
    series_data = await service.get_item(series_id)
    if not series_data:
        raise HTTPException(status_code=404, detail="无法获取上级剧集详情")

    provider_ids = series_data.get('ProviderIds', {})
    tmdb_id = provider_ids.get('Tmdb')
    series_name = series_data.get('Name', '未知')

    if not tmdb_id:
        logger.warning(f"┗ ⚠️ 剧集 '{series_name}' 未绑定 TMDB ID")
        raise HTTPException(status_code=404, detail=f"剧集 '{series_name}' 暂无 TMDB ID 绑定")

    process_time = (time.time() - start_time) * 1000
    audit_log("TMDB 反向溯源成功", process_time, [
        f"单集 ID: {episode_id}",
        f"归属剧集: {series_name}",
        f"定位 TMDB: {tmdb_id}"
    ])
    
    return {
        "series_name": series_name,
        "tmdb_id": tmdb_id,
        "series_id": series_id,
        "item_type": series_data.get("Type")
    }
