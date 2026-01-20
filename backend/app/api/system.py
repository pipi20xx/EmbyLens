from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from app.utils.logger import get_log_dates, get_log_content, LOG_DIR
from datetime import datetime
import os
import httpx
from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from app.utils.logger import get_log_dates, get_log_content, LOG_DIR
from datetime import datetime

router = APIRouter()

CURRENT_VERSION = "v1.0.8"
DOCKER_IMAGE = "pipi20xx/embylens"

@router.get("/version")
async def check_version():
    """检测 Docker Hub 上的最新版本"""
    latest_version = CURRENT_VERSION
    has_update = False
    
    try:
        # Docker Hub API: 获取 tags，按最后更新时间排序
        url = f"https://hub.docker.com/v2/repositories/{DOCKER_IMAGE}/tags/?page_size=5&ordering=last_updated"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                tags = data.get("results", [])
                # 过滤掉 'latest' 标签，寻找版本号标签 (通常是 v 开头或数字)
                for tag in tags:
                    tag_name = tag.get("name")
                    if tag_name and tag_name != "latest":
                        latest_version = tag_name
                        break
                
                # 简单比较（如果不同则认为有更新，实际可能需要更复杂的版本号对比）
                if latest_version != CURRENT_VERSION:
                    has_update = True
    except Exception as e:
        # 如果网络不通或 API 变动，静默失败，返回当前版本
        pass

    return {
        "current": CURRENT_VERSION,
        "latest": latest_version,
        "has_update": has_update
    }

@router.get("/logs/dates")
async def fetch_log_dates():
    return get_log_dates()

@router.get("/logs/content/{date}")
async def fetch_log_content(date: str):
    # 此接口返回 JSON 供弹窗列表渲染
    return {"content": get_log_content(date)}

@router.get("/logs/raw", response_class=PlainTextResponse)
async def fetch_raw_log(type: str = Query("monitor")):
    """日志接口：返回当前最新的原始文本日志 (倒序，最新在上)"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    content = get_log_content(current_date)
    # 按行分割，反转，再合并
    lines = content.splitlines()
    lines.reverse()
    return "\n".join(lines)

@router.get("/logs/export/{date}", response_class=PlainTextResponse)
async def export_log_by_date(date: str):
    """按日期返回原始文本日志"""
    return get_log_content(date)