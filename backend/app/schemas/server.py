from pydantic import BaseModel
from typing import Optional

class ServerConfig(BaseModel):
    name: str = "默认服务器"
    url: str
    api_key: str
    user_id: Optional[str] = None
    tmdb_api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    session_token: Optional[str] = None

class ServerResponse(ServerConfig):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class ConnectionTest(BaseModel):
    url: str
    api_key: str