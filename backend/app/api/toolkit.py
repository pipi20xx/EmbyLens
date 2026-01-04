from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.models.server import EmbyServer
from app.services.emby import EmbyService
from app.utils.logger import logger, audit_log
import time

router = APIRouter()

# 定义字典仅为防止某些逻辑引用报错，但在 adder/mapper 中不再强制自动填充
GENRE_ID_MAP = {
    "动作": 28, "冒险": 12, "动画": 16, "喜剧": 35, "犯罪": 80,
    "纪录": 99, "纪录片": 99, "剧情": 18, "家庭": 10751, "奇幻": 14,
    "历史": 36, "恐怖": 27, "音乐": 10402, "悬疑": 9648, "爱情": 10749,
    "科幻": 878, "电视电影": 10770, "惊悚": 53, "战争": 10752, "西部": 37
}

class GenreMapping(BaseModel):
    old: str
    new_name: str
    new_id: Optional[str] = None # 改为完全可选

class BaseMetadataRequest(BaseModel):
    lib_names: List[str]
    dry_run: bool = True

class GenreMapperRequest(BaseMetadataRequest):
    genre_mappings: List[GenreMapping]

class GenreRemoverRequest(BaseMetadataRequest):
    genres_to_remove: List[str]

class GenreAdderRequest(BaseMetadataRequest):
    genre_to_add_name: str
    genre_to_add_id: Optional[str] = None

class PeopleRemoverRequest(BaseMetadataRequest):
    item_types: List[str] = ["Movie", "Series"]
    lib_names: List[str]
    dry_run: bool = True

class MetadataUnlockerRequest(BaseMetadataRequest):
    item_types: List[str]
    lib_names: List[str]
    dry_run: bool = True

class MetadataManagerResponse(BaseModel):
    message: str
    processed_count: int
    dry_run_active: bool

async def get_emby_context(db: AsyncSession):
    result = await db.execute(select(EmbyServer).limit(1))
    server = result.scalars().first()
    if not server: raise HTTPException(status_code=400, detail="未配置服务器")
    return EmbyService(server.url, server.api_key, server.user_id, server.tmdb_api_key), server.user_id

async def _get_library_id(service: EmbyService, lib_name: str) -> Optional[str]:
    resp = await service._request("GET", "/Library/VirtualFolders")
    if resp and resp.status_code == 200:
        for f in resp.json():
            if f.get("Name") == lib_name: return f.get("ItemId")
    return None

async def _get_lib_items(service: EmbyService, parent_id: str, item_types: List[str]) -> List[Dict]:
    params = {'ParentId': parent_id, 'Fields': 'Genres,GenreItems,LockedFields,LockData,People', 'IncludeItemTypes': ",".join(item_types), 'Recursive': 'true'}
    resp = await service._request("GET", "/Items", params=params)
    return resp.json().get('Items', []) if resp and resp.status_code == 200 else []

async def _get_full_item(service: EmbyService, user_id: str, item_id: str) -> Optional[Dict]:
    params = {"Fields": "Genres,GenreItems,People,LockedFields,LockData,ChannelMappingInfo"}
    endpoint = f"/Users/{user_id}/Items/{item_id}" if user_id else f"/Items/{item_id}"
    resp = await service._request("GET", endpoint, params=params)
    return resp.json() if resp and resp.status_code == 200 else None

# --- 1:1 复刻实装 ---

@router.post("/mapper", response_model=MetadataManagerResponse)
async def genre_mapper(request: GenreMapperRequest, db: AsyncSession = Depends(get_db)):
    service, user_id = await get_emby_context(db)
    processed = 0
    start_time = time.time()
    
    # 建立映射字典：如果不填 ID，则 Id 值为 None
    mapping_dict = {}
    for m in request.genre_mappings:
        mapping_dict[m.old] = {
            "Name": m.new_name, 
            "Id": int(m.new_id) if (m.new_id and m.new_id.isdigit()) else None
        }

    for lib_name in request.lib_names:
        parent_id = await _get_library_id(service, lib_name)
        if not parent_id: continue
        items = await _get_lib_items(service, parent_id, ["Movie", "Series"])
        for it_list in items:
            full_item = await _get_full_item(service, user_id, it_list["Id"])
            if not full_item: continue
            
            genres = full_item.get("Genres", [])
            if any(g in mapping_dict for g in genres):
                processed += 1
                if not request.dry_run:
                    # 1. 更新字符串列表
                    full_item["Genres"] = list(set([mapping_dict[g]["Name"] if g in mapping_dict else g for g in genres]))
                    # 2. 更新对象列表：如果不填 ID，则生成的对象只有 Name
                    new_gi = []
                    for gi in full_item.get("GenreItems", []):
                        gn = gi.get("Name")
                        if gn in mapping_dict:
                            m = mapping_dict[gn]
                            item_obj = {"Name": m["Name"]}
                            if m["Id"] is not None: item_obj["Id"] = m["Id"]
                            new_gi.append(item_obj)
                        else: new_gi.append(gi)
                    full_item["GenreItems"] = new_gi
                    await service.update_item(full_item["Id"], full_item)
                logger.info(f"┃  ┣ 🎯 {'[预览]' if request.dry_run else '[执行]'} 修改项目: {full_item.get('Name')}")
    return MetadataManagerResponse(message="操作完成", processed_count=processed, dry_run_active=request.dry_run)

@router.post("/genre_adder", response_model=MetadataManagerResponse)
async def genre_adder(request: GenreAdderRequest, db: AsyncSession = Depends(get_db)):
    service, user_id = await get_emby_context(db)
    processed = 0
    start_time = time.time()
    logger.info(f"🚀 开始 [类型新增] 任务: {request.genre_to_add_name}")
    
    # 严格逻辑：如果不填 ID 就是 None
    new_id = int(request.genre_to_add_id) if (request.genre_to_add_id and request.genre_to_add_id.isdigit()) else None

    for lib_name in request.lib_names:
        parent_id = await _get_library_id(service, lib_name)
        if not parent_id: continue
        items = await _get_lib_items(service, parent_id, ["Movie", "Series"])
        for it_list in items:
            full_item = await _get_full_item(service, user_id, it_list["Id"])
            if not full_item: continue
            
            genres = full_item.get("Genres", [])
            if request.genre_to_add_name not in genres:
                processed += 1
                if not request.dry_run:
                    full_item["Genres"] = genres + [request.genre_to_add_name]
                    gi_list = full_item.get("GenreItems", [])
                    new_gi_obj = {"Name": request.genre_to_add_name}
                    if new_id is not None: new_gi_obj["Id"] = new_id
                    gi_list.append(new_gi_obj)
                    full_item["GenreItems"] = gi_list
                    await service.update_item(full_item["Id"], full_item)
                logger.info(f"┃  ┣ 🎯 新增到项目: {full_item.get('Name')}")
    return MetadataManagerResponse(message="添加完成", processed_count=processed, dry_run_active=request.dry_run)

# ... 其余 Remover, Locker 等逻辑保持 1:1 复刻 ...
@router.post("/remover", response_model=MetadataManagerResponse)
async def genre_remover(request: GenreRemoverRequest, db: AsyncSession = Depends(get_db)):
    service, user_id = await get_emby_context(db)
    processed = 0
    start_time = time.time()
    to_remove = request.genres_to_remove
    for lib_name in request.lib_names:
        parent_id = await _get_library_id(service, lib_name)
        if not parent_id: continue
        items = await _get_lib_items(service, parent_id, ["Movie", "Series"])
        for it_list in items:
            full_item = await _get_full_item(service, user_id, it_list["Id"])
            if not full_item: continue
            original_genres = full_item.get("Genres", [])
            should_modify = (not to_remove and original_genres) or (to_remove and any(g in to_remove for g in original_genres))
            if should_modify:
                processed += 1
                if not request.dry_run:
                    full_item["Genres"] = [g for g in original_genres if g not in to_remove] if to_remove else []
                    full_item["GenreItems"] = [gi for gi in full_item.get("GenreItems", []) if gi.get("Name") not in to_remove] if to_remove else []
                    await service.update_item(full_item["Id"], full_item)
                logger.info(f"┃  ┣ 🎯 修改项目: {full_item.get('Name')}")
    return MetadataManagerResponse(message="移除成功", processed_count=processed, dry_run_active=request.dry_run)

@router.post("/people_remover", response_model=MetadataManagerResponse)
async def people_remover(request: PeopleRemoverRequest, db: AsyncSession = Depends(get_db)):
    service, user_id = await get_emby_context(db)
    processed = 0
    for lib_name in request.lib_names:
        parent_id = await _get_library_id(service, lib_name)
        if not parent_id: continue
        items = await _get_lib_items(service, parent_id, request.item_types)
        for it_list in items:
            full_item = await _get_full_item(service, user_id, it_list["Id"])
            if full_item and full_item.get("People"):
                processed += 1
                if not request.dry_run:
                    full_item["People"] = []
                    await service.update_item(it_list["Id"], full_item)
    return MetadataManagerResponse(message="操作完成", processed_count=processed, dry_run_active=request.dry_run)

@router.post("/metadata_field_unlocker", response_model=MetadataManagerResponse)
async def metadata_field_unlocker(request: MetadataUnlockerRequest, db: AsyncSession = Depends(get_db)):
    service, user_id = await get_emby_context(db)
    processed = 0
    for lib_name in request.lib_names:
        parent_id = await _get_library_id(service, lib_name)
        if not parent_id: continue
        items = await _get_lib_items(service, parent_id, request.item_types)
        for it_list in items:
            full_item = await _get_full_item(service, user_id, it_list["Id"])
            if not full_item: continue
            if full_item.get("LockedFields") or full_item.get("LockData"):
                processed += 1
                if not request.dry_run:
                    full_item["LockedFields"] = []; full_item["LockData"] = False
                    await service.update_item(full_item["Id"], full_item)
    return MetadataManagerResponse(message="操作完成", processed_count=processed, dry_run_active=request.dry_run)

@router.post("/item_locker", response_model=MetadataManagerResponse)
async def item_locker(request: MetadataUnlockerRequest, db: AsyncSession = Depends(get_db)):
    service, user_id = await get_emby_context(db)
    processed = 0
    for lib_name in request.lib_names:
        parent_id = await _get_library_id(service, lib_name)
        if not parent_id: continue
        items = await _get_lib_items(service, parent_id, request.item_types)
        for it_list in items:
            full_item = await _get_full_item(service, user_id, it_list["Id"])
            if not full_item: continue
            if not full_item.get("LockData"):
                processed += 1
                if not request.dry_run:
                    full_item["LockData"] = True
                    await service.update_item(full_item["Id"], full_item)
    return MetadataManagerResponse(message="操作完成", processed_count=processed, dry_run_active=request.dry_run)

@router.post("/item_unlocker", response_model=MetadataManagerResponse)
async def item_unlocker(request: MetadataUnlockerRequest, db: AsyncSession = Depends(get_db)):
    return await metadata_field_unlocker(request, db)

@router.post("/episode_deleter", response_model=MetadataManagerResponse)
async def episode_deleter(request: BaseMetadataRequest, db: AsyncSession = Depends(get_db)):
    service, user_id = await get_emby_context(db)
    processed = 0
    for lib_name in request.lib_names:
        parent_id = await _get_library_id(service, lib_name)
        if not parent_id: continue
        items = await _get_lib_items(service, parent_id, ["Episode"])
        for it_list in items:
            full_item = await _get_full_item(service, user_id, it_list["Id"])
            if full_item and (full_item.get("Genres") or full_item.get("GenreItems")):
                processed += 1
                if not request.dry_run:
                    full_item["Genres"] = []; full_item["GenreItems"] = []
                    await service.update_item(full_item["Id"], full_item)
    return MetadataManagerResponse(message="操作完成", processed_count=processed, dry_run_active=request.dry_run)
