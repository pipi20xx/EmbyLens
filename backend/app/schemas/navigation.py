from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str
    order: Optional[int] = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    class Config:
        from_attributes = True

class SiteNavBase(BaseModel):
    title: str
    url: str
    icon: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    category: Optional[str] = "默认"
    order: Optional[int] = 0

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