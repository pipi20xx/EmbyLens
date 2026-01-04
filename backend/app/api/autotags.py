from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
from app.core.config_manager import get_config, save_config
from app.core.tagger import Tagger
from app.utils.logger import logger, audit_log
from .autotag_helper import AutotagEmbyHelper
from app.utils.http_client import get_async_client
import httpx
import time
import uuid
import asyncio
import json

router = APIRouter()

# --- 全量复刻：Webhook 队列与后台处理 ---
webhook_queue = asyncio.Queue()

# --- 1:1 复刻原项目的国家/语言映射表 ---
LANG_TO_COUNTRY = {
    "en": "美国", "zh": "中国大陆", "ja": "日本", "ko": "韩国", "fr": "法国", "de": "德国",
    "es": "西班牙", "it": "意大利", "hi": "印度", "ar": "沙特阿拉伯", "pt": "巴西", "ru": "俄罗斯",
    "th": "泰国", "sv": "瑞典", "da": "丹麦", "no": "挪威", "nl": "荷兰", "pl": "波兰",
}

# 扩展映射：支持从 ISO 国家代码映射到中文
COUNTRY_CODE_TO_NAME = {
    "JP": "日本", "CN": "中国大陆", "US": "美国", "KR": "韩国", "TW": "中国台湾", "HK": "中国香港",
    "FR": "法国", "DE": "德国", "GB": "英国", "IT": "意大利", "ES": "西班牙", "CA": "加拿大",
    "IN": "印度", "TH": "泰国", "RU": "俄罗斯", "BR": "巴西", "AU": "澳大利亚"
}

# --- 请求模型 ---
class AutoTagRule(BaseModel):
    name: str
    tag: str
    item_type: str = "all"
    match_all_conditions: bool = False
    is_negative_match: bool = False
    conditions: Dict[str, Any]

class TagActionRequest(BaseModel):
    mode: Literal['merge', 'overwrite'] = 'merge'
    library_type: Literal['all', 'favorite'] = 'all'
    custom_tags: Optional[List[str]] = None

async def get_helper():
    config = get_config()
    url = config.get("url")
    if not url: raise HTTPException(status_code=400, detail="未配置 Emby 服务器")
    token = config.get("session_token") or config.get("api_key")
    return AutotagEmbyHelper(url, token, config.get("user_id")), config

async def fetch_tmdb_details(tmdb_key: str, tmdb_id: str, media_type: str):
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}"
    params = {"api_key": tmdb_key, "language": "zh-CN"}
    async with get_async_client(timeout=15.0) as client:
        try:
            logger.info(f"┃  ┃  🌐 [TMDB] 发起请求: {url}")
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warning(f"┃  ┃  ⚠️ TMDB API 响应异常: {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"┃  ┃  ❌ TMDB 请求失败: {str(e)}")
            return None

# --- Webhook 处理核心逻辑 (1:1 结构复刻) ---

async def process_webhook_item(payload: Dict):
    """处理来自 Webhook 的单个项目"""
    config = get_config()
    wh_cfg = config.get("webhook", {})
    if not wh_cfg.get("automation_enabled"): 
        logger.info("┃  [Webhook] 自动处理已关闭，跳过执行")
        return
    
    # 1. 获取项目信息
    item = payload.get("Item", {})
    item_id = item.get("Id")
    item_name = item.get("Name")
    item_type = item.get("Type")
    
    # 特殊处理：如果是剧集(Episode)或季度(Season)，转而处理其所属的剧集系列(Series)
    if item_type in ["Episode", "Season"]:
        series_id = item.get("SeriesId")
        if series_id:
            logger.info(f"┃  📺 检测到{item_type}入库，将自动处理其所属剧集系列 (ID: {series_id})")
            # 重新获取系列的信息
            helper, _ = await get_helper()
            series_item = await helper.get_item_full_detail(series_id)
            if series_item:
                item = series_item
                item_id = series_id
                item_name = item.get("Name")
                item_type = item.get("Type")
            else:
                logger.error(f"┃  ❌ 无法获取所属剧集系列详情: {series_id}")
                return

    tmdb_id = item.get("ProviderIds", {}).get("Tmdb")
    
    if not tmdb_id:
        logger.warning(f"┃  ⚠️ [Webhook] 项目缺少 TMDB ID，无法自动化: {item_name} (Type: {item_type})")
        return
        
    if item_type not in ["Movie", "Series"]: 
        return
    
    # 延迟执行，等待 Emby 元数据同步完成
    delay = wh_cfg.get("delay_seconds", 10)
    logger.info(f"⏳ [Webhook] 任务启动，等待 {delay}s 以确保 Emby 元数据就绪: {item_name}")
    await asyncio.sleep(delay)
    
    # 2. 执行打标签逻辑
    helper, _ = await get_helper()
    tagger = Tagger(config.get("autotag_rules", []))
    tmdb_key = config.get("tmdb_api_key")
    
    m_type = "movie" if item_type == "Movie" else "tv"
    logger.info(f"┃  ┣ 🌐 [Webhook TMDB] 正在获取详情: {item_name} (TMDB ID: {tmdb_id})")
    details = await fetch_tmdb_details(tmdb_key, tmdb_id, m_type)
    if not details: 
        logger.error(f"┃  ┃  ❌ [Webhook TMDB] 获取详情失败: {item_name}")
        return
    
    # 元数据解析
    genre_ids = [str(g["id"]) for g in details.get("genres", [])]
    genre_names = [g["name"] for g in details.get("genres", [])]
    countries = [c.upper() for c in details.get("origin_country", [])]
    
    year_str = details.get("release_date") or details.get("first_air_date") or "0000"
    year = int(year_str[:4]) if year_str else 0
    
    props = {"countries": countries, "genre_names": genre_ids, "year": year, "type": item_type}
    
    log_countries = [COUNTRY_CODE_TO_NAME.get(c, c) for c in countries]
    logger.info(f"┃  ┃  📋 [Webhook 元数据] 国家: {log_countries} ({countries}) | 类型: {genre_names} ({genre_ids}) | 年份: {year}")
    
    target_tags = tagger.generate_tags(props)
    if target_tags:
        logger.info(f"┃  ┃  🎯 [Webhook 匹配] 目标标签: {target_tags}")
        await helper.update_item_metadata(item_id, target_tags, wh_cfg.get("write_mode", "merge"))
    else:
        logger.info(f"┃  ┃  🟡 [Webhook 跳过] 无规则匹配: {item_name}")

async def webhook_worker():
    """无限循环的后台 Webhook 消费者"""
    logger.info("📡 [Webhook] 自动标签后台监听已启动")
    while True:
        payload = await webhook_queue.get()
        try:
            await process_webhook_item(payload)
        except Exception as e:
            logger.error(f"❌ [Webhook] 处理失败: {e}")
        finally:
            webhook_queue.task_done()

# --- 任务执行流 (1:1 结构复刻) ---

async def run_autotag_task_isolated(request: TagActionRequest):
    helper, config = await get_helper()
    tagger = Tagger(config.get("autotag_rules", []))
    tmdb_key = config.get("tmdb_api_key")
    logger.info(f"🚀 [自动标签] 任务启动...")
    
    all_items = await helper.get_all_items()
    if request.library_type == 'favorite': 
        all_items = [i for i in all_items if i.get("UserData", {}).get("IsFavorite")]
        logger.info(f"┃  ⭐ 已过滤仅限收藏项目，待处理数量: {len(all_items)}")
    else:
        logger.info(f"┃  📦 待处理总数: {len(all_items)}")

    updated = 0
    for i, item in enumerate(all_items):
        item_name = item.get("Name", "Unknown")
        item_id = item.get("Id")
        try:
            tmdb_id = item.get("ProviderIds", {}).get("Tmdb")
            if not tmdb_id:
                logger.info(f"┃  🕒 [{i+1}/{len(all_items)}] 跳过 (无 TMDB ID): {item_name}")
                continue
            
            logger.info(f"┃  🕒 [{i+1}/{len(all_items)}] 正在处理: {item_name}")
            
            m_type = "movie" if item.get("Type") == "Movie" else "tv"
            details = await fetch_tmdb_details(tmdb_key, tmdb_id, m_type)
            if not details:
                logger.warning(f"┃  ┃  ⚠️ 跳过: 无法获取 TMDB 详情")
                continue

            # --- 元数据解析 ---
            genre_ids = [str(g["id"]) for g in details.get("genres", [])]
            genre_names = [g["name"] for g in details.get("genres", [])]
            
            # 国家：直接使用 ISO 代码进行匹配
            countries = [c.upper() for c in details.get("origin_country", [])]
            
            # 如果没有国家代码，尝试从原始语言映射（作为兜底）
            if not countries:
                lang = details.get("original_language")
                # 这里依然可以用映射，但存入 props 的应该是代码
                # 为了简化，我们直接用 details 里的原始数据
                pass

            year_str = details.get("release_date") or details.get("first_air_date") or "0000"
            year = int(year_str[:4]) if year_str else 0
            
            # props 现在存储 ID 和 CODE
            props = {"countries": countries, "genre_names": genre_ids, "year": year, "type": item.get("Type")}
            
            # 日志输出：转换回中文方便人类阅读
            log_countries = [COUNTRY_CODE_TO_NAME.get(c, c) for c in countries]
            logger.info(f"┃  ┃  📋 [元数据] 国家: {log_countries} ({countries}) | 类型: {genre_names} ({genre_ids}) | 年份: {year}")
            
            target_tags = request.custom_tags if request.custom_tags else tagger.generate_tags(props)
            
            if target_tags:
                logger.info(f"┃  ┃  🎯 [匹配] 目标标签: {target_tags}")
                if await helper.update_item_metadata(item_id, target_tags, request.mode): 
                    updated += 1
            else:
                logger.info(f"┃  ┃  🟡 [跳过] 无规则匹配")

        except Exception as e:
            logger.error(f"┃  ┃  ❌ 处理出错 [{item_name}]: {str(e)}")
        
        # 强制小休，避免请求过快
        if i % 5 == 0: await asyncio.sleep(0.1)
        
    logger.info(f"✅ [自动标签] 完成，更新: {updated}")

async def run_clear_task_isolated(tags_to_remove: Optional[List[str]] = None):
    helper, _ = await get_helper()
    logger.warning(f"🔥 [标签清理] 启动")
    all_items = await helper.get_all_items()
    logger.info(f"┃  📦 扫描完成，待处理项目数: {len(all_items)}")
    
    cleared = 0
    for i, item in enumerate(all_items):
        item_name = item.get("Name", "Unknown")
        try:
            if tags_to_remove is None:
                # 清理所有标签
                if await helper.update_item_metadata(item["Id"], [], mode='overwrite'): 
                    cleared += 1
            else:
                # 清理指定标签
                if await helper.remove_specific_tags(item["Id"], tags_to_remove): 
                    cleared += 1
        except Exception as e:
            logger.error(f"┃  ┃  ❌ 清理出错 [{item_name}]: {str(e)}")
            
        if i > 0 and i % 50 == 0:
            logger.info(f"┃  🕒 清理进度: {i}/{len(all_items)}...")
            
    logger.info(f"✅ [标签清理] 结束，影响项目数: {cleared}")

# --- 路由接口 ---

@router.post("/webhook/{token}")
async def receive_webhook(token: str, payload: Dict = Body(...)):
    """接收并分发 Webhook"""
    wh_cfg = get_config().get("webhook", {})
    event = payload.get("Event")
    item = payload.get("Item", {})
    item_name = item.get("Name", "Unknown")
    
    # 第一时间打出收到的所有 Webhook 概要，不带任何过滤
    logger.info(f"📡 [Webhook] 收到请求 | 事件: {event} | 项目: {item_name} | Token校验: {'通过' if token == wh_cfg.get('secret_token') else '失败'}")
    
    # 打印完整 Payload 供用户排查
    logger.info(f"📦 [Webhook Payload] 原始数据明细:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")

    if not wh_cfg.get("enabled"): 
        logger.warning(f"┃  ⚠️ Webhook 功能在设置中已被禁用")
        raise HTTPException(status_code=403, detail="Webhook disabled")
        
    if token != wh_cfg.get("secret_token"): 
        logger.error(f"┃  ❌ 提供的 Token ({token}) 与配置不匹配")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # 扩大匹配范围，记录下具体被忽略的原因
    target_events = ["item.added", "ItemAdded", "LibraryChanged", "library.new"]
    if event in target_events:
        logger.info(f"┃  ✅ 命中目标事件，已入队等待处理...")
        await webhook_queue.put(payload)
        return {"status": "queued"}
    
    logger.info(f"┃  🟡 忽略非自动化目标事件: {event}")
    return {"status": "ignored", "event": event}

@router.get("/rules")
async def get_rules(): return get_config().get("autotag_rules", [])

@router.post("/rules")
async def save_rules(rules: List[AutoTagRule]):
    config = get_config()
    config["autotag_rules"] = [r.dict() for r in rules]
    save_config(config)
    return {"message": "ok"}

@router.post("/test-write")
async def test_tag_write(item_id: str = Body(..., embed=True), tag: str = Body(..., embed=True)):
    helper, _ = await get_helper()
    return {"success": await helper.update_item_metadata(item_id, [tag], mode='merge')}

@router.post("/execute")
async def execute_task(request: TagActionRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_autotag_task_isolated, request)
    return {"message": "ok"}

@router.post("/clear-all")
async def clear_all(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_clear_task_isolated, None)
    return {"message": "ok"}

@router.post("/clear-specific")
async def clear_specific(tags: List[str] = Body(..., embed=True), background_tasks: BackgroundTasks = None):
    background_tasks.add_task(run_clear_task_isolated, tags)
    return {"message": "ok"}

@router.get("/webhook-config")
async def get_wh_config():
    wh = get_config().get("webhook", {})
    return wh

@router.post("/webhook-config")
async def save_wh_config(data: Dict = Body(...)):
    config = get_config()
    config["webhook"] = data
    save_config(config)
    return {"message": "ok"}