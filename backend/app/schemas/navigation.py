from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str
    icon: Optional[str] = None
    order: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    icon: Optional[str] = None
    class Config:
        from_attributes = True

class SiteNavBase(BaseModel):
    title: str
    url: str
    icon: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    category: Optional[str] = "默认"
    order: Optional[int] = None

class SiteNavCreate(SiteNavBase):
    pass

class SiteNavUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    category: Optional[str] = None
    order: Optional[int] = None

class SiteNavResponse(SiteNavBase):

    id: int

    class Config:

        from_attributes = True



# ==========================================

# 书签相关 Schema

# ==========================================



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



# 启用递归类型支持

BookmarkResponse.update_forward_refs()
