from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional, Any
import json
import os
import uuid
import httpx
import re
import zipfile
import shutil
import tempfile
from datetime import datetime
from urllib.parse import urljoin, urlparse

from app.utils.http_client import get_async_client
from app.services import navigation_service as nav_service
from app.schemas.navigation import (
    SiteNavCreate, SiteNavUpdate, SiteNavResponse,
    CategoryCreate, CategoryResponse
)

router = APIRouter()

ICON_DIR = "/app/data/nav_icons"
BG_DIR = "/app/data/nav_backgrounds"
os.makedirs(ICON_DIR, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)

# ==========================================
# 设置管理 API
# ==========================================

@router.get("/settings")
async def get_settings():
    return nav_service.get_nav_data().get("settings", {})

@router.put("/settings")
async def update_settings(settings: dict):
    return nav_service.update_settings(settings)

@router.post("/upload-bg")
async def upload_background(file: UploadFile = File(...)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    
    mime_map = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/x-png": ".png",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "image/gif": ".gif"
    }
    
    if not ext and file.content_type in mime_map:
        ext = mime_map[file.content_type]

    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif']
    if ext not in allowed_extensions:
        if file.content_type and file.content_type.startswith("image/"):
            ext = mime_map.get(file.content_type, ".jpg")
        else:
            raise HTTPException(status_code=400, detail="只支持图片格式")
    
    # 清理旧背景
    if os.path.exists(BG_DIR):
        for old_file in os.listdir(BG_DIR):
            try: os.remove(os.path.join(BG_DIR, old_file))
            except: pass

    filename = f"bg_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(BG_DIR, filename)
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    url = f"/nav_backgrounds/{filename}"
    nav_service.update_settings({"background_url": url})
    return {"url": url}

@router.post("/upload-icon")
async def upload_icon(file: UploadFile = File(...)):
    # 提取扩展名
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    
    # 映射 content-type 到扩展名
    mime_map = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/pjpeg": ".jpg",
        "image/png": ".png",
        "image/x-png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "image/x-icon": ".ico",
        "image/vnd.microsoft.icon": ".ico",
        "image/bmp": ".bmp",
        "image/x-ms-bmp": ".bmp"
    }
    
    # 如果没有扩展名，尝试从 content-type 推断
    if not ext and file.content_type in mime_map:
        ext = mime_map[file.content_type]
    
    # 允许更多常见的图片格式
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.ico', '.gif', '.bmp']
    
    print(f"[Navigation] Uploading icon: {filename}, ext: {ext}, content_type: {file.content_type}")

    if ext not in allowed_extensions:
        # 最后一次机会：如果 content-type 是图片，即使扩展名不认识也允许
        if file.content_type and file.content_type.startswith("image/"):
            # 如果是未知的图片类型，默认用 .png 或者是从 mime_map 获取
            ext = mime_map.get(file.content_type, ".png")
        else:
            print(f"[Navigation] Unsupported format: {ext} / {file.content_type}")
            raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext or '无扩展名'} ({file.content_type})")
    
    filename = f"custom_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(ICON_DIR, filename)
    
    try:
        content = await file.read()
        print(f"[Navigation] File read, size: {len(content)} bytes")
        with open(filepath, "wb") as f:
            f.write(content)
        print(f"[Navigation] Icon saved to: {filepath}")
    except Exception as e:
        print(f"[Navigation] Save error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    return {"icon": f"/nav_icons/{filename}"}

# ==========================================
# 辅助工具函数
# ==========================================

async def download_and_cache_icon(url: str) -> Optional[str]:
    """下载远程图标并保存到本地 nav_icons 目录"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        async with get_async_client(timeout=10.0, headers=headers, use_proxy=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                # 识别扩展名
                ext = ".png"
                ctype = resp.headers.get("content-type", "").lower()
                if "image/svg" in ctype: ext = ".svg"
                elif "image/x-icon" in ctype: ext = ".ico"
                elif "image/webp" in ctype: ext = ".webp"
                elif "image/jpeg" in ctype: ext = ".jpg"
                
                filename = f"{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(ICON_DIR, filename)
                
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                return f"/nav_icons/{filename}"
    except Exception as e:
        print(f"[Navigation] Icon download failed: {e}")
    return None

# ==========================================
# 分类管理 API
# ==========================================

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories():
    return nav_service.list_categories()

@router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate):
    cat_id = nav_service.add_category(category.name)
    return {"id": cat_id, "name": category.name, "order": 0}

@router.put("/categories/{cat_id}")
async def update_category(cat_id: int, category: CategoryCreate):
    nav_service.update_category(cat_id, category.name)
    return {"message": "Updated"}

@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: int):
    nav_service.delete_category(cat_id)
    nav_service.cleanup_orphaned_icons() 
    return {"message": "Deleted"}

@router.post("/categories/reorder")
async def reorder_categories(ordered_ids: List[int]):
    nav_service.reorder_categories(ordered_ids)
    return {"message": "Reordered"}

# ==========================================
# 站点管理 API
# ==========================================

@router.get("/", response_model=List[SiteNavResponse])
async def list_sites():
    return nav_service.list_sites()

@router.post("/", response_model=SiteNavResponse)
async def create_site(site: SiteNavCreate):
    # 自动本地化远程图标
    site_data = site.dict()
    icon = site_data.get("icon")
    if icon and icon.startswith(("http://", "https://")):
        local_path = await download_and_cache_icon(icon)
        if local_path:
            site_data["icon"] = local_path
            
    return nav_service.add_site(site_data)

@router.put("/{site_id}")
async def update_site(site_id: int, site: SiteNavUpdate):
    # 自动本地化远程图标
    site_data = site.dict(exclude_unset=True)
    icon = site_data.get("icon")
    if icon and icon.startswith(("http://", "https://")):
        local_path = await download_and_cache_icon(icon)
        if local_path:
            site_data["icon"] = local_path
            
    nav_service.update_site(site_id, site_data)
    nav_service.cleanup_orphaned_icons() 
    return {"message": "Updated"}

@router.delete("/{site_id}")
async def delete_site(site_id: int):
    nav_service.delete_site(site_id)
    nav_service.cleanup_orphaned_icons() 
    return {"message": "Deleted"}

@router.post("/reorder")
async def reorder_sites(ordered_ids: List[int]):
    nav_service.reorder_sites(ordered_ids)
    return {"message": "Reordered"}

# ==========================================
# 备份与恢复 API
# ==========================================

@router.get("/export")
async def export_navigation():
    """导出包含 JSON 配置和所有本地图标的 ZIP 包"""
    temp_zip = tempfile.mktemp(suffix=".zip")
    try:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. 写入配置
            if os.path.exists(nav_service.NAV_FILE):
                zf.write(nav_service.NAV_FILE, "navigation.json")
            else:
                zf.writestr("navigation.json", json.dumps(nav_service.DEFAULT_NAV))
            
            # 2. 写入图标目录
            if os.path.exists(ICON_DIR):
                for file in os.listdir(ICON_DIR):
                    fpath = os.path.join(ICON_DIR, file)
                    if os.path.isfile(fpath):
                        zf.write(fpath, os.path.join("nav_icons", file))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return FileResponse(
            path=temp_zip, 
            filename=f"lens_nav_backup_{timestamp}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_navigation(file: UploadFile = File(...)):
    """从 ZIP 包恢复配置和图标"""
    temp_dir = tempfile.mkdtemp()
    temp_zip = os.path.join(temp_dir, "upload.zip")
    try:
        with open(temp_zip, "wb") as f:
            f.write(await file.read())
            
        with zipfile.ZipFile(temp_zip, 'r') as zf:
            if "navigation.json" not in zf.namelist():
                raise HTTPException(status_code=400, detail="非法备份包：缺失 navigation.json")
            
            zf.extractall(temp_dir)
            
            # 1. 搬运图标
            zip_icons_path = os.path.join(temp_dir, "nav_icons")
            if os.path.exists(zip_icons_path):
                for fname in os.listdir(zip_icons_path):
                    shutil.copy2(os.path.join(zip_icons_path, fname), os.path.join(ICON_DIR, fname))
            
            # 2. 覆盖配置
            shutil.copy2(os.path.join(temp_dir, "navigation.json"), nav_service.NAV_FILE)
            
        nav_service.cleanup_orphaned_icons() 
        return {"message": "全量恢复成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ==========================================
# 增强型图标抓取
# ==========================================

@router.get("/bing-wallpaper")
async def get_bing_wallpaper(
    index: int = 0, 
    mkt: str = "zh-CN",
    resolution: str = "1920x1080"
):
    """获取必应每日壁纸及其元数据"""
    try:
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx={index}&n=1&mkt={mkt}"
        async with get_async_client(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if "images" in data and len(data["images"]) > 0:
                    image = data["images"][0]
                    # 构建完整图片 URL
                    base_url = f"https://www.bing.com{image['urlbase']}_{resolution}.jpg"
                    return {
                        "url": base_url,
                        "title": image.get("title", ""),
                        "copyright": image.get("copyright", ""),
                        "copyrightlink": image.get("copyrightlink", "")
                    }
    except Exception as e:
        print(f"Fetch bing error: {e}")
    return {"error": "Failed to fetch"}

@router.get("/fetch-icon")
async def fetch_icon(url: str = Query(...)):
    """抓取网页图标并自动本地化"""
    if not url.startswith(("http://", "https://")):
        url = 'https://' + url
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    remote_icon_url = None
    try:
        async with get_async_client(timeout=10.0, headers=headers, use_proxy=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                html = resp.text
                # 匹配所有 <link> 标签
                links = re.findall(r'<link\s+[^>]*>', html, re.I)
                potential_icons = []
                for link in links:
                    if re.search(r'rel=[\""](.*?icon.*?)[\""]', link, re.I):
                        href_match = re.search(r'href=[\""](.*?)[\""]', link, re.I)
                        if href_match: potential_icons.append(href_match.group(1))
                
                if potential_icons:
                    # 优先选高清格式
                    best = potential_icons[0]
                    for icon in potential_icons:
                        if any(x in icon.lower() for x in ['.png', '.svg', '.webp']):
                            best = icon
                            break
                    remote_icon_url = urljoin(url, best)
                else:
                    # 搜寻 img logo
                    img_match = re.search(r'<img[^>]*src=[\""]([^\""]*(?:logo|icon)[^\""]*)[\""]', html, re.I)
                    if img_match: remote_icon_url = urljoin(url, img_match.group(1))

        # 兜底 favicon.ico
        if not remote_icon_url:
            parsed = urlparse(url)
            remote_icon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

        # 下载到本地
        local_path = await download_and_cache_icon(remote_icon_url)
        return {"icon": local_path or remote_icon_url}
            
    except Exception:
        parsed = urlparse(url)
        remote_icon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
        local_path = await download_and_cache_icon(remote_icon_url)
        return {"icon": local_path or remote_icon_url}