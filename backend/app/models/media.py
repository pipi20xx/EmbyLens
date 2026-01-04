from sqlalchemy import Column, Integer, String, JSON, Boolean, Float
from app.db.session import Base

class MediaItem(Base):
    __tablename__ = "media_items"
    id = Column(String, primary_key=True, index=True) # Emby ID
    server_id = Column(Integer, index=True)
    name = Column(String, index=True)
    item_type = Column(String, index=True) # Movie, Series, Season, Episode
    tmdb_id = Column(String, index=True, nullable=True)
    path = Column(String)
    year = Column(Integer, nullable=True)
    parent_id = Column(String, index=True, nullable=True)
    
    # 新增：编号信息，用于单集精准查重
    season_num = Column(Integer, nullable=True)
    episode_num = Column(Integer, nullable=True)
    
    # 媒体规格信息 (从 MediaStreams 提取)
    display_title = Column(String, nullable=True)
    video_codec = Column(String, nullable=True)
    video_range = Column(String, nullable=True)
    audio_codec = Column(String, nullable=True)
    
    raw_data = Column(JSON) # 完整的 Emby 响应 JSON

class DedupeRule(Base):
    __tablename__ = "dedupe_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    priority_order = Column(JSON) # ["display_title", "video_codec", ...]
    values_weight = Column(JSON) # {"display_title": ["4k", "2160p"], ...}
    tie_breaker = Column(String, default="small_id")
    is_default = Column(Boolean, default=False)
