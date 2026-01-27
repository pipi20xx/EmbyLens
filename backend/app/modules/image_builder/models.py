from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class BuildTaskLog(Base):
    __tablename__ = "build_task_logs"
    id = Column(String, primary_key=True, index=True) # task_id
    project_id = Column(String, index=True, nullable=False)
    tag = Column(String, nullable=False)
    status = Column(String, default="PENDING", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())