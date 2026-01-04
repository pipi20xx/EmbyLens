from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.server import EmbyServer
from app.services.emby import EmbyService
from app.utils.logger import logger, audit_log
from sqlalchemy import select
import time

router = APIRouter()

async def get_active_emby(db: AsyncSession):
    result = await db.execute(select(EmbyServer).limit(1))
    server = result.scalars().first()
    if not server:
        logger.error("❌ 任务终止: 未发现配置。请在系统设置中填入 IP 和 API Key")
        raise HTTPException(status_code=400, detail="未配置服务器")
    return EmbyService(server.url, server.api_key, server.user_id, server.tmdb_api_key)

@router.get("/reverse-tmdb", summary="根据单集 ID 反查剧集 TMDB")
async def reverse_lookup_tmdb(
    episode_id: str = Query(..., description="Emby 单集 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    1:1 源码复刻 + 深度日志集成
    """
    start_time = time.time()
    logger.info(f"🚀 启动 [剧集 TMDB 反查] 任务 (单集 ID: {episode_id})")

    # 使用统一辅助函数
    service = await get_active_emby(db)
    
    # 步骤 1
    logger.info(f"┣ 🔍 步骤 1: 正在追溯上级剧集 (SeriesId)...")
    episode_data = await service.get_item(episode_id)
    if not episode_data:
        logger.error(f"┗ ❌ 溯源中断: 单集 {episode_id} 不存在")
        raise HTTPException(status_code=404, detail="单集未找到")
    
    series_id = episode_data.get('SeriesId')
    if not series_id:
        logger.warning(f"┗ ⚠️ 溯源中断: 该项目不是剧集单集")
        raise HTTPException(status_code=400, detail="该 ID 没有上级剧集")

    # 步骤 2
    logger.info(f"┣ 🔗 步骤 2: 正在获取剧集详情 (Series ID: {series_id})...")
    series_data = await service.get_item(series_id)
    if not series_data:
        logger.error(f"┗ ❌ 溯源中断: 无法访问上级剧集")
        raise HTTPException(status_code=404, detail="无法获取剧集详情")

    provider_ids = series_data.get('ProviderIds', {})
    tmdb_id = provider_ids.get('Tmdb')
    series_name = series_data.get('Name', '未知')

    if not tmdb_id:
        logger.warning(f"┗ ⚠️ 溯源失败: 剧集 '{series_name}' 未绑定 TMDB ID")
        raise HTTPException(status_code=404, detail=f"未找到 TMDB 绑定")

    audit_log("TMDB 反向溯源成功", (time.time() - start_time) * 1000, [
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
