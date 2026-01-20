from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import httpx
import re
import os
import uuid
from urllib.parse import urljoin, urlparse

from app.services import navigation_service as nav_service
from app.schemas.navigation import (
    SiteNavCreate, SiteNavUpdate, SiteNavResponse,
    CategoryCreate, CategoryResponse
)

router = APIRouter()

ICON_DIR = "/app/data/nav_icons"
os.makedirs(ICON_DIR, exist_ok=True)

# --- 工具函数：下载并缓存图标 ---
async def download_and_cache_icon(url: str) -> Optional[str]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers, verify=False) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                # 获取文件后缀
                ext = ".png"
                content_type = resp.headers.get("content-type", "").lower()
                if "image/svg" in content_type: ext = ".svg"
                elif "image/x-icon" in content_type: ext = ".ico"
                elif "image/webp" in content_type: ext = ".webp"
                elif "image/jpeg" in content_type: ext = ".jpg"
                elif "image/png" in content_type: ext = ".png"
                
                # 生成唯一文件名
                filename = f"{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(ICON_DIR, filename)
                
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                
                # 返回前端可访问的相对路径 (确保有开头的斜杠)
                return f"/nav_icons/{filename}"
    except Exception as e:
        print(f"Download icon failed: {e}")
    return None

# --- 分类管理 ---
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(): return nav_service.list_categories()

@router.post("/categories")
async def create_category(category: CategoryCreate):
    cat_id = nav_service.add_category(category.name)
    return {"id": cat_id, "name": category.name}

@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: int):
    nav_service.delete_category(cat_id)
    return {"message": "Deleted"}

@router.post("/categories/reorder")
async def reorder_categories(ordered_ids: List[int]):
    nav_service.reorder_categories(ordered_ids)
    return {"message": "Reordered"}

# --- 站点管理 ---
@router.get("/", response_model=List[SiteNavResponse])
async def list_sites(): return nav_service.list_sites()

@router.post("/", response_model=SiteNavResponse)
async def create_site(site: SiteNavCreate): return nav_service.add_site(site.dict())

@router.put("/{site_id}")
async def update_site(site_id: int, site: SiteNavUpdate):
    nav_service.update_site(site_id, site.dict(exclude_unset=True))
    return {"message": "Updated"}

@router.delete("/{site_id}")
async def delete_site(site_id: int):
    nav_service.delete_site(site_id)
    return {"message": "Deleted"}

@router.post("/reorder")
async def reorder_sites(ordered_ids: List[int]):
    nav_service.reorder_sites(ordered_ids)
    return {"message": "Reordered"}

# --- 增强版图标抓取工具 ---

@router.get("/fetch-icon")
async def fetch_icon(url: str = Query(...)):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    remote_icon_url = None
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers, verify=False) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                html = resp.text
                links = re.findall(r'<link\s+[^>]*>', html, re.I)
                potential_icons = []
                for link in links:
                    if re.search(r'rel=["\"](.*?icon.*?)["\"]', link, re.I):
                        href_match = re.search(r'href=["\"](.*?)["\"]', link, re.I)
                        if href_match: potential_icons.append(href_match.group(1))
                
                if potential_icons:
                    best_icon = potential_icons[0]
                    for icon in potential_icons:
                        if any(ext in icon.lower() for ext in ['.png', '.svg', '.webp']):
                            best_icon = icon
                            break
                    remote_icon_url = urljoin(url, best_icon)
                else:
                    logo_match = re.search(r'<img[^>]*src=["\"]([^"\"]*(?:logo|icon)[^"\"]*)["\"]', html, re.I)
                    if logo_match: remote_icon_url = urljoin(url, logo_match.group(1))

        if not remote_icon_url:
            parsed = urlparse(url)
            remote_icon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

        local_path = await download_and_cache_icon(remote_icon_url)
        return {"icon": local_path or remote_icon_url}
            
    except Exception:
        parsed = urlparse(url)
        remote_icon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
        local_path = await download_and_cache_icon(remote_icon_url)
        return {"icon": local_path or remote_icon_url}