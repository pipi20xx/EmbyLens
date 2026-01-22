from pydantic import BaseModel
from typing import List, Optional

class NotificationBot(BaseModel):
    id: str
    name: str
    type: str = "telegram"
    token: str
    chat_id: str
    enabled: bool = True
    subscribed_events: List[str] = []
    # 新增交互字段
    is_interactive: bool = False  # 是否开启交互功能
    allowed_user_ids: List[str] = []  # 允许操作的 TG 用户 ID 列表

class NotificationSettings(BaseModel):
    enabled: bool = False
    bots: List[NotificationBot] = []

class TestMessageRequest(BaseModel):
    bot_id: str
    message: str = "这是一条来自 Lens 的测试消息"
