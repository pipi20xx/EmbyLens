from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from app.core.config_manager import get_config
from app.utils.http_client import get_async_client
from app.utils.logger import logger, audit_log
import time

router = APIRouter()

async def get_bangumi_config():
    config = get_config()
    token = config.get("bangumi_api_token")
    # Bangumi API token is optional for some public endpoints but recommended
    return token

@router.get("/search", summary="Bangumi 关键词搜索")
async def search_bangumi(
    keywords: str = Query(..., description="搜索关键词"),
    type: int = Query(2, description="条目类型: 1-书籍, 2-动画, 3-音乐, 4-游戏, 6-三次元"),
    offset: int = Query(0, description="偏移量"),
    limit: int = Query(10, description="限制数量")
):
    start_time = time.time()
    token = await get_bangumi_config()
    
    # 使用 Bangumi 搜索 API
    url = f"https://api.bgm.tv/search/subject/{keywords}"
    params = {
        "type": type,
        "max_results": limit,
        "start": offset,
        "responseGroup": "medium"
    }
    
    headers = {"User-Agent": "EmbyLens/1.0.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with get_async_client(use_proxy=True) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code != 200:
                return {"results": [], "total": 0}
            
            data = response.json()
            # 统一结构返回
            results = data.get("list", [])
            return {"results": results, "total": data.get("results", 0)}
    except Exception as e:
        logger.error(f"❌ Bangumi 搜索异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subject/{subject_id}", summary="获取 Bangumi 条目详情")
async def get_subject(subject_id: int):
    start_time = time.time()
    token = await get_bangumi_config()
    
    url = f"https://api.bgm.tv/v0/subjects/{subject_id}"
    headers = {"User-Agent": "EmbyLens/1.0.0 (https://github.com/YourRepo/EmbyLens)"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with get_async_client(use_proxy=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ Bangumi 获取条目失败: {response.text}")
                return {"error": "Bangumi API 返回错误", "details": response.json() if response.content else response.text}
            
            data = response.json()
            return data
    except Exception as e:
        logger.error(f"❌ Bangumi 获取条目异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subject/{subject_id}/characters", summary="获取 Bangumi 角色列表")
async def get_characters(subject_id: int):
    start_time = time.time()
    token = await get_bangumi_config()
    
    url = f"https://api.bgm.tv/v0/subjects/{subject_id}/characters"
    headers = {"User-Agent": "EmbyLens/1.0.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with get_async_client(use_proxy=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return {"error": "Bangumi API 返回错误", "details": response.text}
            
            data = response.json()
            return data
    except Exception as e:
        logger.error(f"❌ Bangumi 获取角色异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/episodes", summary="获取 Bangumi 章节列表")
async def get_episodes(
    subject_id: int = Query(..., description="条目 ID"),
    type: Optional[int] = Query(None, description="章节类型: 0-本篇, 1-特别篇, 2-OP, 3-ED, 4-预告/宣传, 5-MAD, 6-其他"),
    offset: int = Query(0, description="偏移量"),
    limit: int = Query(100, description="限制数量")
):
    start_time = time.time()
    token = await get_bangumi_config()
    
    url = f"https://api.bgm.tv/v0/episodes"
    params = {
        "subject_id": subject_id,
        "offset": offset,
        "limit": limit
    }
    if type is not None:
        params["type"] = type
        
    headers = {"User-Agent": "EmbyLens/1.0.0 (https://github.com/YourRepo/EmbyLens)"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with get_async_client(use_proxy=True) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ Bangumi 获取章节失败: {response.text}")
                return {"error": "Bangumi API 返回错误", "details": response.json() if response.content else response.text}
            
            data = response.json()
            return data
    except Exception as e:
        logger.error(f"❌ Bangumi 获取章节异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
