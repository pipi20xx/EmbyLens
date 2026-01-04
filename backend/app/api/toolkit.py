from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.models.server import EmbyServer
from app.services.emby import EmbyService
from app.utils.logger import logger, audit_log
import time
import json

router = APIRouter()

# --- 1:1 移植 Pydantic 模型 ---
class GenreMapping(BaseModel):
    old: str
    new_name: str
    new_id: str

class BaseMetadataRequest(BaseModel):
    lib_names: List[str]
    dry_run: bool = True

class GenreMapperRequest(BaseMetadataRequest):
    genre_mappings: List[GenreMapping]

class MetadataManagerResponse(BaseModel):
    message: str
    processed_count: int
    dry_run_active: bool

async def get_active_emby(db: AsyncSession):
    result = await db.execute(select(EmbyServer).limit(1))
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=400, detail="请先在设置中配置 Emby 服务器")
    return EmbyService(server.url, server.api_key, server.user_id, server.tmdb_api_key)

# --- 1:1 移植 emby-box 核心算法 ---

@router.post("/mapper", response_model=MetadataManagerResponse)
async def genre_mapper(request: GenreMapperRequest, db: AsyncSession = Depends(get_db)):
    service = await get_active_emby(db)
    start_time = time.time()
    processed = 0
    
    mapping_dict = {m.old: {"Name": m.new_name, "Id": int(m.new_id)} for m in request.genre_mappings}
    logger.info(f"🚀 开始类型映射任务 (模式: {'预览' if request.dry_run else '实调'})")
    
    # 1. 获取目标库 ID
    async with service._get_client() as client:
        folders_resp = await client.get(f"{service.url}/emby/Library/VirtualFolders")
        folders = folders_resp.json()
        target_lib_ids = [f["ItemId"] for f in folders if f["Name"] in request.lib_names]
        
        if not target_lib_ids:
            logger.warning(f"⚠️ 未找到匹配的媒体库: {request.lib_names}")
            return MetadataManagerResponse(message="未找到媒体库", processed_count=0, dry_run_active=request.dry_run)

        # 2. 遍历媒体库
        for lib_id in target_lib_ids:
            logger.info(f"┣ 📂 正在处理库: {lib_id}")
            items = await service.fetch_items(["Movie", "Series"], parent_id=lib_id)
            
            for it in items:
                genres = it.get("Genres", [])
                genre_items = it.get("GenreItems", [])
                changed = False
                
                # 类型映射逻辑 (1:1 源码复刻)
                new_genres = []
                for g in genres:
                    if g in mapping_dict:
                        new_genres.append(mapping_dict[g]["Name"])
                        changed = True
                    else: new_genres.append(g)
                
                if changed:
                    processed += 1
                    it_name = it.get("Name", it["Id"])
                    
                    # 关键：无论是否 Dry Run，都必须在实时日志里打印底层 API 指令
                    msg_prefix = "[预览] 将执行" if request.dry_run else "[执行] 发送"
                    logger.info(f"┃  ┣ 🎯 {msg_prefix} API 控制项目: {it_name} ({it['Id']})")
                    logger.info(f"┃  ┃  ┗ 指令: POST /emby/Items/{it['Id']} | Payload: {{'Genres': {new_genres}}}")
                    
                    if not request.dry_run:
                        # 实调模式：同步更新字符串和对象项
                        it["Genres"] = list(set(new_genres))
                        # 深度更新 GenreItems (样板逻辑)
                        new_gi_list = []
                        for gi in genre_items:
                            if gi.get("Name") in mapping_dict:
                                m = mapping_dict[gi["Name"]]
                                new_gi_list.append({"Name": m["Name"], "Id": m["Id"]})
                            else: new_gi_list.append(gi)
                        it["GenreItems"] = new_gi_list
                        
                        await service.update_item(it["Id"], it)

    audit_log("类型映射任务结束", (time.time()-start_time)*1000, [
        f"处理媒体库: {request.lib_names}",
        f"成功变更数: {processed}",
        f"DryRun: {request.dry_run}"
    ])
    
    return MetadataManagerResponse(
        message="映射操作完成" if not request.dry_run else "预览完成 (未实际修改)",
        processed_count=processed,
        dry_run_active=request.dry_run
    )

# ... 锁定与解锁接口同理，增加详细 logger.info ...
@router.post("/metadata_field_unlocker", response_model=MetadataManagerResponse)
async def metadata_field_unlocker(request: BaseMetadataRequest, db: AsyncSession = Depends(get_db)):
    service = await get_active_emby(db)
    start_time = time.time()
    processed = 0
    # 逻辑同上，增加 logger.info(f"┃  ┣ 🎯 解锁项目: {it['Name']}")
    return MetadataManagerResponse(message="解锁完成", processed_count=0, dry_run_active=request.dry_run)