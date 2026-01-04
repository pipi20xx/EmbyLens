from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from app.db.session import get_db
from app.models.server import EmbyServer
from app.models.media import DedupeRule
from app.schemas.server import ServerConfig, ConnectionTest, ServerResponse
from app.services.emby import EmbyService
from app.utils.logger import logger, audit_log
import time

router = APIRouter()

@router.post("/test")
async def test_connection(config: ConnectionTest):
    service = EmbyService(config.url, config.api_key)
    success = await service.test_connection()
    if not success:
        raise HTTPException(status_code=400, detail="无法连接到 Emby 服务器")
    return {"message": "连接成功"}

@router.post("/save", response_model=ServerResponse)
async def save_config(config: ServerConfig, db: AsyncSession = Depends(get_db)):
    """单服务器模式：始终只维护一条 ID=1 的记录"""
    start_time = time.time()
    
    # 查找现有的第一条配置
    result = await db.execute(select(EmbyServer).limit(1))
    server = result.scalars().first()
    
    if server:
        # 更新现有配置
        server.name = config.name
        server.url = config.url
        server.api_key = config.api_key
        server.user_id = config.user_id
        server.tmdb_api_key = config.tmdb_api_key
    else:
        # 创建新配置
        server = EmbyServer(
            id=1, # 强制固定 ID
            name=config.name,
            url=config.url,
            api_key=config.api_key,
            user_id=config.user_id,
            tmdb_api_key=config.tmdb_api_key,
            is_active=True
        )
        db.add(server)
    
    await db.commit()
    await db.refresh(server)
    
    audit_log("系统配置已更新", (time.time() - start_time) * 1000, [
        f"服务器: {server.url}",
        f"UserID: {server.user_id or '未设置'}",
        f"TMDB Key: {'已配置' if server.tmdb_api_key else '未配置'}"
    ])
    
    return server

@router.get("/current", response_model=Optional[ServerResponse])
async def get_current_config(db: AsyncSession = Depends(get_db)):
    """获取当前唯一的服务器配置"""
    result = await db.execute(select(EmbyServer).limit(1))
    return result.scalars().first()