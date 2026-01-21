from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from app.db.session import Base
from datetime import datetime

class BackupHistory(Base):
    __tablename__ = "backup_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), index=True) # 对应 config.json 中的任务 ID
    task_name = Column(String(100))
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20)) # 'running', 'success', 'failed'
    mode = Column(String(20)) # '7z', 'tar', 'sync'
    size = Column(Float, default=0) # 备份大小 (MB)
    file_count = Column(Integer, default=0)
    message = Column(Text, nullable=True) # 错误信息或摘要
    output_path = Column(String(500), nullable=True)
