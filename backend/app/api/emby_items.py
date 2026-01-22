from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config_manager import get_config
from app.services.emby import EmbyService, get_emby_service
from app.utils.logger import logger, audit_log
import time

router = APIRouter()

@router.get("/info")
async def get_item_info(item_id: str, db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    service = get_emby_service()
    if not service:
        raise HTTPException(status_code=400, detail="未配置 Emby 服务器")
    
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="条目未找到")
        
    process_time = (time.time() - start_time) * 1000
    audit_log("项目元数据查询成功", process_time, [
        f"Item ID: {item_id}",
        f"名称: {item.get('Name')}"
    ])
    return item

@router.get("/query")
async def query_item(item_id: str, db: AsyncSession = Depends(get_db)):
    # 兼容旧接口名称
    return await get_item_info(item_id, db)