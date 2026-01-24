from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TerminalHostBase(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str = "root"
    auth_type: str = "password"
    password: Optional[str] = None
    private_key: Optional[str] = None
    private_key_password: Optional[str] = None

class TerminalHostCreate(TerminalHostBase):
    pass

class TerminalHostUpdate(TerminalHostBase):
    name: Optional[str] = None
    host: Optional[str] = None

class TerminalHostRead(TerminalHostBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class QuickCommandBase(BaseModel):
    title: str
    command: str
    description: Optional[str] = None

class QuickCommandCreate(QuickCommandBase):
    pass

class QuickCommandRead(QuickCommandBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
