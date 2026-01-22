from fastapi import APIRouter, HTTPException
from typing import List
from app.core.config_manager import get_config, save_config
from app.schemas.notification import NotificationBot, NotificationSettings, TestMessageRequest
from app.services.notification_service import NotificationService
from app.services.telegram_bot_worker import TelegramBotWorker
import uuid

router = APIRouter()

@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings():
    config = get_config()
    return config.get("notification_settings", {"enabled": False, "bots": []})

@router.post("/settings")
async def save_notification_settings(settings: NotificationSettings):
    config = get_config()
    config["notification_settings"] = settings.dict()
    save_config(config)
    
    # 重新启动所有 Bot (会先停止旧的)
    await TelegramBotWorker.start_all()
    
    return {"status": "success"}

@router.post("/bots")
async def add_bot(bot: NotificationBot):
    config = get_config()
    settings = config.get("notification_settings", {"enabled": False, "bots": []})
    
    # 如果 ID 为空则生成
    if not bot.id:
        bot.id = str(uuid.uuid4())
    
    settings["bots"].append(bot.dict())
    config["notification_settings"] = settings
    save_config(config)
    
    # 如果开启了交互，启动监听
    if bot.enabled and bot.is_interactive:
        await TelegramBotWorker.start_bot(bot.dict())
        
    return bot

@router.put("/bots/{bot_id}")
async def update_bot(bot_id: str, bot: NotificationBot):
    config = get_config()
    settings = config.get("notification_settings", {"enabled": False, "bots": []})
    
    bots = settings.get("bots", [])
    for i, b in enumerate(bots):
        if b["id"] == bot_id:
            bots[i] = bot.dict()
            break
    else:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    settings["bots"] = bots
    config["notification_settings"] = settings
    save_config(config)
    
    # 更新监听状态
    if bot.enabled and bot.is_interactive:
        await TelegramBotWorker.start_bot(bot.dict())
    else:
        await TelegramBotWorker.stop_bot(bot_id)
        
    return bot

@router.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str):
    config = get_config()
    settings = config.get("notification_settings", {"enabled": False, "bots": []})
    
    bots = settings.get("bots", [])
    new_bots = [b for b in bots if b["id"] != bot_id]
    
    settings["bots"] = new_bots
    config["notification_settings"] = settings
    save_config(config)
    
    # 停止监听
    await TelegramBotWorker.stop_bot(bot_id)
    
    return {"status": "success"}

@router.post("/test")
async def test_bot(req: TestMessageRequest):
    config = get_config()
    settings = config.get("notification_settings", {"enabled": False, "bots": []})
    bots = settings.get("bots", [])
    
    bot = next((b for b in bots if b["id"] == req.bot_id), None)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    success, msg = await NotificationService.send_telegram_message(
        bot["token"], 
        bot["chat_id"], 
        f"🔔 *测试通知*\n\n{req.message}"
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"status": "success"}
