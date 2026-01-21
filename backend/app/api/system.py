from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from app.utils.logger import get_log_dates, get_log_content, LOG_DIR
from datetime import datetime
import os
from app.utils.http_client import get_async_client

router = APIRouter()

CURRENT_VERSION = "v1.0.9"
DOCKER_IMAGE = "pipi20xx/embylens"

@router.get("/version")
async def check_version():
    """检测 Docker Hub 上的最新版本"""
    # 统一处理本地版本号，移除可能存在的 v 前缀
    local_ver = CURRENT_VERSION.lstrip('v').strip()
    latest_version = local_ver
    has_update = False
    
    try:
        # 使用配置了代理的客户端
        url = f"https://hub.docker.com/v2/repositories/{DOCKER_IMAGE}/tags/?page_size=5&ordering=last_updated"
        async with get_async_client(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                tags = data.get("results", [])
                
                for tag in tags:
                    tag_name = tag.get("name")
                    if tag_name and tag_name != "latest":
                        # 统一移除远程版本号的 v 前缀进行比较
                        remote_ver = tag_name.lstrip('v').strip()
                        latest_version = remote_ver
                        
                        # 如果远程版本不等于本地版本
                        if remote_ver != local_ver:
                            # 简单的字符串大小比较或拆分比较
                            try:
                                remote_parts = [int(p) for p in remote_ver.split('.')]
                                local_parts = [int(p) for p in local_ver.split('.')]
                                if remote_parts > local_parts:
                                    has_update = True
                            except:
                                # 如果解析失败，回退到简单的非等比较
                                if remote_ver != local_ver:
                                    has_update = True
                        break
    except Exception:
        pass

    return {
        "current": f"v{local_ver}",
        "latest": f"v{latest_version}",
        "has_update": has_update,
        "docker_hub": f"https://hub.docker.com/r/{DOCKER_IMAGE}"
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