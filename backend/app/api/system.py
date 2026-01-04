from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from app.utils.logger import get_log_dates, get_log_content, LOG_DIR
from datetime import datetime
import os

router = APIRouter()

@router.get("/logs/dates")
async def fetch_log_dates():
    return get_log_dates()

@router.get("/logs/content/{date}")
async def fetch_log_content(date: str):
    # 此接口返回 JSON 供弹窗列表渲染
    return {"content": get_log_content(date)}

@router.get("/logs/raw", response_class=PlainTextResponse)
async def fetch_raw_log(type: str = Query("monitor")):
    """复刻样板：返回当前最新的原始文本日志"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    content = get_log_content(current_date)
    return content

@router.get("/logs/export/{date}", response_class=PlainTextResponse)
async def export_log_by_date(date: str):
    """按日期返回原始文本日志"""
    return get_log_content(date)