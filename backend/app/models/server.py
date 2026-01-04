from sqlalchemy import Column, Integer, String, Boolean
from app.db.session import Base

class EmbyServer(Base):
    __tablename__ = "emby_servers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Default Server")
    url = Column(String)
    api_key = Column(String)
    user_id = Column(String, nullable=True) # 新增：Emby User ID
    tmdb_api_key = Column(String, nullable=True) # 新增：TMDB API Key
    user_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)