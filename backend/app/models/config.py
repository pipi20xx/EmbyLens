from sqlalchemy import Column, String, Boolean, Text
from app.db.session import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=True)
    description = Column(String(200), nullable=True)
