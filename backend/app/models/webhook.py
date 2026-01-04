from sqlalchemy import Column, Integer, String, JSON, DateTime
from app.db.session import Base
from datetime import datetime

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True) # 如 playback.start, library.new
    source_ip = Column(String)
    payload = Column(JSON) # 存储完整的原始 JSON
    created_at = Column(DateTime, default=datetime.now)
