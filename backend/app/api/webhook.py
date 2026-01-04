from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from app.db.session import get_db
from app.models.webhook import WebhookLog
from app.utils.logger import logger, audit_log
from typing import List, Dict, Any
import json
import time

router = APIRouter()

@router.post("/receive/{full_path:path}", summary="接收 Emby Webhook (支持后缀)")
@router.post("/receive", summary="接收 Emby Webhook")
async def receive_webhook(request: Request, full_path: str = "", db: AsyncSession = Depends(get_db)):
    """
    接收来自 Emby 的 Webhook，并物理持久化原始 JSON
    """
    start_time = time.time()
    source_ip = request.client.host if request.client else "unknown"
    logger.info(f"🚀 收到 Webhook 信号: 来自 {source_ip}")
    
    if full_path:
        logger.info(f"┣ 🏷️ 识别到路径后缀: /{full_path}")

    # 1. 载荷提取与解析
    payload = {}
    try:
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            logger.info(f"┣ 📦 识别为 Multipart 封装格式")
            form_data = await request.form()
            payload_str = form_data.get("data", "{}")
            payload = json.loads(payload_str)
        else:
            logger.info(f"┣ 📦 识别为纯 JSON 格式")
            payload = await request.json()
    except Exception as e:
        logger.error(f"┗ ❌ 载荷解析严重失败: {e}")
        return {"status": "error", "message": "Parse Error"}

    # 2. 字段提取
    event_type = payload.get("Event", "unknown")
    item_name = payload.get('Item', {}).get('Name', 'N/A')
    user_name = payload.get('User', {}).get('Name', 'N/A')

    # 3. 物理持久化
    try:
        new_log = WebhookLog(
            event_type=event_type,
            source_ip=source_ip,
            payload=payload
        )
        db.add(new_log)
        await db.commit()
        logger.info(f"┣ 💾 原始载荷已物理持久化至 SQLite (Event: {event_type})")
    except Exception as e:
        logger.error(f"┣ ❌ 数据库写入异常: {e}")

    # 4. 全链路审计汇报
    process_time = (time.time() - start_time) * 1000
    audit_log(f"Webhook 捕获: {event_type}", process_time, [
        f"来源: {source_ip} (/{full_path if full_path else ''})",
        f"项目: {item_name}",
        f"用户: {user_name}",
        f"载荷大小: {len(str(payload))} 字符"
    ])

    return {"status": "ok"}

@router.get("/list", summary="查询 Webhook 历史日志")
async def get_webhook_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    
    result = await db.execute(
        select(WebhookLog).order_by(desc(WebhookLog.created_at)).limit(limit)
    )
    logs = result.scalars().all()
    
    audit_log("加载 Webhook 日志库", (time.time() - start_time) * 1000, [
        f"请求限额: {limit}",
        f"检索记录数: {len(logs)}"
    ])
    
    return logs

@router.delete("/clear", summary="清空 Webhook 历史记录")
async def clear_webhook_logs(db: AsyncSession = Depends(get_db)):
    """物理清空 Webhook 日志表"""
    start_time = time.time()
    
    # 获取清空前的计数用于审计
    count_res = await db.execute(select(WebhookLog))
    before_count = len(count_res.scalars().all())
    
    await db.execute(delete(WebhookLog))
    await db.commit()
    
    audit_log("Webhook 数据库重置", (time.time() - start_time) * 1000, [
        f"操作类型: 全库清空",
        f"清理记录数: {before_count}"
    ])
    return {"success": True, "cleared_count": before_count}