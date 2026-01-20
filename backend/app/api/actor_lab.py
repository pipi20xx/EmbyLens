from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import re
import time
from app.core.config_manager import get_config
from app.utils.http_client import get_async_client
from app.utils.logger import logger, audit_log

router = APIRouter()

async def get_tmdb_key():
    config = get_config()
    key = config.get("tmdb_api_key")
    if not key:
        raise HTTPException(status_code=400, detail="未配置 TMDB API Key")
    return key

def get_origin_name_smart(data: Dict[str, Any]) -> str:
    """智能原名推断逻辑"""
    place = data.get('place_of_birth', '') or ''
    akas = data.get('also_known_as', [])
    default_name = data.get('name', '未知')
    
    if not akas:
        return default_name

    # 正则规则
    regex_han = re.compile(r'[\u4e00-\u9fa5]')
    regex_kana = re.compile(r'[\u3040-\u30ff]')
    regex_hangul = re.compile(r'[\uac00-\ud7af]')
    regex_cyrillic = re.compile(r'[\u0400-\u04FF]')

    target_script = None
    if any(k in place for k in ["China", "Hong Kong", "Taiwan", "Beijing", "Shanghai", "Canton"]):
        target_script = "chinese"
    elif any(k in place for k in ["Japan", "Tokyo", "Osaka", "Kyoto", "Okinawa"]):
        target_script = "japanese"
    elif any(k in place for k in ["Korea", "Seoul", "Busan"]):
        target_script = "korean"
    elif any(k in place for k in ["Russia", "Soviet", "Ukraine", "Moscow"]):
        target_script = "cyrillic"
    elif any(k in place for k in ["Thai", "Bangkok"]):
        target_script = "thai"

    found_name = None
    for aka in akas:
        if target_script == "chinese":
            if regex_han.search(aka) and not regex_kana.search(aka) and not regex_hangul.search(aka):
                found_name = aka
                break 
        elif target_script == "japanese":
            if regex_kana.search(aka):
                found_name = aka
                break
            elif regex_han.search(aka) and not found_name:
                found_name = aka
        elif target_script == "korean":
            if regex_hangul.search(aka):
                found_name = aka
                break
        elif target_script == "cyrillic":
            if regex_cyrillic.search(aka):
                found_name = aka
                break
    
    if not found_name and not any(k in place for k in ["USA", "United Kingdom", "Canada", "Australia"]):
        for aka in akas:
            if any(ord(c) > 127 for c in aka):
                found_name = aka
                break
                
    return found_name if found_name else default_name

@router.get("/analyze", summary="演员信息深度探测")
async def analyze_actor(
    person_id: str = Query(..., description="TMDB Person ID"),
    language: Optional[str] = Query("zh-CN", description="主语言"),
    include_translations: bool = Query(True, description="是否包含翻译池")
):
    start_time = time.time()
    tmdb_key = await get_tmdb_key()
    
    append_items = ["combined_credits", "external_ids", "images"]
    if include_translations:
        append_items.append("translations")
        
    url = f"https://api.themoviedb.org/3/person/{person_id}"
    params = {
        "api_key": tmdb_key,
        "append_to_response": ",".join(append_items)
    }
    if language:
        params["language"] = language

    try:
        async with get_async_client(use_proxy=True) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="TMDB API 请求失败")
            
            data = resp.json()
            
            # 1. 提取姓名
            main_name = data.get('name', '未知')
            origin_name = get_origin_name_smart(data)
            
            # 2. 提取中文名
            chinese_name = main_name
            for t in data.get('translations', {}).get('translations', []):
                if t.get('iso_639_1') in ['zh', 'cn']:
                    name = t.get('data', {}).get('name')
                    if name:
                        chinese_name = name
                        break
            
            # 3. 整理姓名池
            name_pool = {main_name, origin_name, chinese_name}
            for aka in data.get('also_known_as', []):
                name_pool.add(aka)
            
            # 4. 整理代表作
            credits = data.get('combined_credits', {}).get('cast', [])
            credits.sort(key=lambda x: x.get('vote_count', 0), reverse=True)
            top_works = []
            for w in credits[:12]:
                top_works.append({
                    "id": w.get('id'),
                    "title": w.get('title') or w.get('name'),
                    "original_title": w.get('original_title') or w.get('original_name'),
                    "release_date": w.get('release_date') or w.get('first_air_date'),
                    "media_type": w.get('media_type'),
                    "poster_path": w.get('poster_path'),
                    "vote_average": w.get('vote_average')
                })

            result = {
                "id": data.get('id'),
                "main_name": main_name,
                "origin_name": origin_name,
                "chinese_name": chinese_name,
                "place_of_birth": data.get('place_of_birth'),
                "birthday": data.get('birthday'),
                "deathday": data.get('deathday'),
                "biography": data.get('biography'),
                "profile_path": data.get('profile_path'),
                "imdb_id": data.get('external_ids', {}).get('imdb_id'),
                "name_pool": sorted(list(name_pool)),
                "top_works": top_works,
                "raw": data
            }
            
            audit_log("演员深度分析完成", (time.time() - start_time) * 1000, [f"ID: {person_id}", f"原名: {origin_name}"])
            return result
            
    except Exception as e:
        logger.error(f"❌ 演员分析异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
