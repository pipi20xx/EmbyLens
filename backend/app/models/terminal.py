from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from app.db.session import Base

class TerminalHost(Base):
    __tablename__ = "terminal_hosts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    host = Column(String(255), nullable=False)  # IP 或 域名
    port = Column(Integer, default=22)
    username = Column(String(100), default="root")
    auth_type = Column(String(20), default="password")  # password 或 key
    password = Column(String(255), nullable=True)
    private_key = Column(Text, nullable=True)
    private_key_password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class QuickCommand(Base):
    __tablename__ = "quick_commands"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    command = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
