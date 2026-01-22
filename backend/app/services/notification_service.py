import httpx
import asyncio
from typing import List, Any, Dict
from app.core.config_manager import get_config
from app.utils.logger import logger

class NotificationService:
    @staticmethod
    async def send_telegram_message(token: str, chat_id: str, text: str):
        """发送 Telegram 消息"""
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "MarkdownV2"
        }
        
        # 针对 MarkdownV2 转义一些特殊字符，防止发送失败
        # TG MarkdownV2 要求极其严格
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        escaped_text = text
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f"\\{char}")

        payload["text"] = escaped_text

        try:
            config = get_config()
            proxy_cfg = config.get("proxy", {})
            proxies = None
            if proxy_cfg.get("enabled") and proxy_cfg.get("url"):
                proxies = proxy_cfg.get("url")
            
            async with httpx.AsyncClient(timeout=10.0, proxies=proxies) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.error(f"❌ [Notification] TG 发送失败 ({resp.status_code}): {resp.text}")
                    return False, resp.text
                return True, "OK"
        except Exception as e:
            logger.error(f"❌ [Notification] TG 发送异常: {e}")
            return False, str(e)

    @classmethod
    async def emit(cls, event: str, title: str, message: str = ""):
        """
        触发通知事件 (乐高积木的核心出口)
        :param event: 事件名称，如 backup.success
        :param title: 通知标题
        :param message: 通知详情内容
        """
        config = get_config()
        settings = config.get("notification_settings", {})
        
        if not settings.get("enabled"):
            return

        bots = settings.get("bots", [])
        active_bots = [b for b in bots if b.get("enabled") and (event in b.get("subscribed_events", []) or "*" in b.get("subscribed_events", []))]

        if not active_bots:
            return

        formatted_text = f"*【{title}】*\n\n{message}"
        
        tasks = []
        for bot in active_bots:
            if bot.get("type") == "telegram":
                tasks.append(cls.send_telegram_message(bot.get("token"), bot.get("chat_id"), formatted_text))
        
        if tasks:
            logger.info(f"📢 [Notification] 正在为事件 '{event}' 分发通知给 {len(tasks)} 个机器人...")
            await asyncio.gather(*tasks)
