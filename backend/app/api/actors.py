from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.server import EmbyServer
from app.services.emby import EmbyService
from app.utils.logger import logger, audit_log
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import time
import httpx

router = APIRouter()

async def get_emby_context(db: AsyncSession):
    result = await db.execute(select(EmbyServer).limit(1))
    server = result.scalars().first()
    if not server: raise HTTPException(status_code=400, detail="未配置服务器")
    return EmbyService(server.url, server.api_key, server.user_id, server.tmdb_api_key), server

async def fetch_tmdb_data(tmdb_key: str, path: str, params: Dict = None):
    if not tmdb_key: raise HTTPException(status_code=400, detail="未配置 TMDB API Key")
    url = f"https://api.themoviedb.org/3{path}"
    base_params = {"api_key": tmdb_key, "language": "zh-CN"}
    if params: base_params.update(params)
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, params=base_params)
        return resp.json() if resp.status_code == 200 else None

# --- 1:1 源码级 API 实装 ---

@router.get("/search-emby", summary="从 Emby 库内搜索演员 (对标 emby-box 扫描逻辑)")
async def search_actor_in_emby(query: str = Query(...), db: AsyncSession = Depends(get_db)):
    """
    1:1 复刻 emby-box 演员查找逻辑：
    如果输入是数字，则执行全库 Person 详情遍历匹配。
    """
    service, _ = await get_emby_context(db)
    start_time = time.time()
    
    if query.isdigit():
        # --- 源码逻辑：全库暴力扫描模式 ---
        logger.info(f"🚀 启动 [Emby 库内 TMDB ID 扫描]: {query}")
        
        # 1. 获取所有演员 ID 列表
        all_actors = await service.fetch_items(["Person"], recursive=True)
        total = len(all_actors)
        logger.info(f"┣ 📂 库内共有 {total} 个演员条目，开始逐一获取详情进行 ID 比对...")
        
        results = []
        for i, actor_summary in enumerate(all_actors):
            aid = actor_summary["Id"]
            # 2. 必须获取详情才能拿到 ProviderIds
            detail = await service.get_item(aid)
            if detail:
                tmdb_id = detail.get("ProviderIds", {}).get("Tmdb")
                if str(tmdb_id) == query:
                    logger.info(f"┃  ┣ ✅ 匹配成功: {detail.get('Name')} (Emby ID: {aid})")
                    results.append(detail)
                    # 原版通常找到第一个就跳出，这里我们遵循原版
                    break
            
            # 进度每 50 个打一次日志，防止刷屏但保持感知
            if i > 0 and i % 50 == 0:
                logger.info(f"┃  🕒 已扫描 {i}/{total} 个项目...")

        if not results:
            logger.warning(f"┗ ⚠️ 全库扫描结束，未找到匹配项")
    else:
        logger.info(f"🚀 启动 [Emby 名称模糊检索]: {query}")
        params = {"SearchTerm": query, "IncludeItemTypes": "Person", "Recursive": "true", "Fields": "Id"}
        resp = await service._request("GET", "/Items", params=params)
        summary_items = resp.json().get("Items", []) if resp else []
        
        # 核心改进：为搜索到的前 20 个结果（防止过多）抓取 100% 完整详情
        results = []
        for it in summary_items[:20]:
            full_detail = await service.get_item(it["Id"])
            if full_detail:
                results.append(full_detail)
    
    audit_log("Emby 检索结束 (100% 详情模式)", (time.time()-start_time)*1000, [f"模式: {'ID扫描' if query.isdigit() else '名称检索'}", f"命中数: {len(results)}"])
    return {"results": results}

@router.get("/search-tmdb", summary="从 TMDB 搜索演员")
async def search_actor_on_tmdb(query: str = Query(...), db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    _, server = await get_emby_context(db)
    if query.isdigit():
        data = await fetch_tmdb_data(server.tmdb_api_key, f"/person/{query}")
        results = [data] if data else []
    else:
        data = await fetch_tmdb_data(server.tmdb_api_key, "/search/person", {"query": query})
        results = data.get("results", []) if data else []
    return {"results": results}

@router.post("/update-actor-name", summary="修改 Emby 库内演员姓名")
async def update_actor_name(
    emby_id: str = Body(..., embed=True),
    new_name: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """1:1 复刻源码：仅修改演员显示名称"""
    service, _ = await get_emby_context(db)
    start_time = time.time()
    
    logger.info(f"🚀 准备更新演员 ID [{emby_id}] 的姓名为: {new_name}")
    
    # 1. 获取详情
    actor_data = await service.get_item(emby_id)
    if not actor_data: raise HTTPException(status_code=404, detail="库内未找到该演员")
    
    # 2. 覆盖名称
    old_name = actor_data.get('Name')
    actor_data['Name'] = new_name
    
    # 3. 提交
    success = await service.update_item(emby_id, actor_data)
    
    if success:
        audit_log("演员改名成功", (time.time()-start_time)*1000, [f"旧名: {old_name}", f"新名: {new_name}"])
        return {"message": "姓名更新成功"}
    
    raise HTTPException(status_code=500, detail="Emby API 提交失败")

@router.post("/update-emby-actor")
async def update_emby_actor(emby_id: str = Body(...), data: Dict = Body(...), db: AsyncSession = Depends(get_db)):
    service, _ = await get_emby_context(db)
    actor_data = await service.get_item(emby_id)
    if not actor_data: raise HTTPException(status_code=404, detail="演员不存在")
    actor_data.update(data)
    success = await service.update_item(emby_id, actor_data)
    return {"success": success}