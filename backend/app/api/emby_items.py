from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.server import EmbyServer
from app.services.emby import EmbyService
from app.utils.logger import logger, audit_log
from sqlalchemy import select
import time

router = APIRouter()

@router.get("/info", summary="根据 Emby Item ID 获取完整元数据")
async def get_item_info(
    item_id: str = Query(..., description="Emby 项目 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    1:1 源码复刻 + 深度日志集成
    """
    start_time = time.time()
    logger.info(f"🚀 启动 [项目 ID 查询] 任务: {item_id}")
    
    # 获取配置
    result = await db.execute(select(EmbyServer).limit(1))
    server = result.scalars().first()
    if not server:
        logger.error("┗ ❌ 任务失败: 未配置服务器")
        raise HTTPException(status_code=400, detail="请先在设置中配置服务器")

    service = EmbyService(server.url, server.api_key, server.user_id)
    
    logger.info(f"┣ 🔍 正在检索 Emby 原始元数据...")
    item_data = await service.get_item(item_id)
    
    if not item_data:
        logger.error(f"┗ ❌ 未找到项目: {item_id}")
        raise HTTPException(status_code=404, detail=f"项目 {item_id} 未找到")

    process_time = (time.time() - start_time) * 1000
    audit_log("项目元数据查询成功", process_time, [
        f"项目 ID: {item_id}",
        f"项目名称: {item_data.get('Name', '未知')}",
        f"类型: {item_data.get('Type', '未知')}",
        f"字段总数: {len(item_data.keys())}"
    ])
    
    return item_data