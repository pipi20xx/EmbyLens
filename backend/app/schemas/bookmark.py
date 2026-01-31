from pydantic import BaseModel
from typing import Optional, List

class BookmarkBase(BaseModel):
    title: str
    type: str  # "file" 或 "folder"
    url: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[int] = 0

class BookmarkCreate(BookmarkBase):
    pass

class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[int] = None

class BookmarkResponse(BookmarkBase):
    id: str
    children: Optional[List["BookmarkResponse"]] = None
    class Config:
        from_attributes = True

BookmarkResponse.update_forward_refs()
