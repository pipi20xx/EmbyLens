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

@router.post("/save-remote-bg")
async def save_remote_background(payload: dict):
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL 不能为空")
    
    print(f"[Navigation] Saving remote background: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    content = None
    ctype = "image/jpeg"
    error_msg = "未知错误"
    
    try:
        # 1. 尝试通过系统定义的代理 Client
        async with get_async_client(timeout=25.0, use_proxy=True) as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            if resp.status_code == 200:
                content = resp.content
                ctype = resp.headers.get("content-type", "").lower()
            else:
                error_msg = f"代理请求失败: {resp.status_code}"
    except Exception as e:
        error_msg = f"代理连接异常: {str(e)}"
        print(f"[Navigation] Save remote bg with proxy failed: {e}")

    if not content:
        try:
            # 2. 尝试直接连接
            async with httpx.AsyncClient(timeout=25.0, verify=False) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                if resp.status_code == 200:
                    content = resp.content
                    ctype = resp.headers.get("content-type", "").lower()
                else:
                    error_msg += f" | 直接请求失败: {resp.status_code}"
        except Exception as e:
            error_msg += f" | 直接连接异常: {str(e)}"
            print(f"[Navigation] Save remote bg direct failed: {e}")

    if not content:
        # 这里返回 400 提示具体错误原因
        raise HTTPException(status_code=400, detail=f"无法获取远程图片: {error_msg}")

    try:
        # 简单识别扩展名
        ext = ".jpg"
        if "png" in ctype: ext = ".png"
        elif "webp" in ctype: ext = ".webp"
        elif "svg" in ctype: ext = ".svg"

        # 确保目录存在
        os.makedirs(BG_DIR, exist_ok=True)

        # 清理旧背景
        for old_file in os.listdir(BG_DIR):
            try: os.remove(os.path.join(BG_DIR, old_file))
            except: pass

        filename = f"bg_fixed_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(BG_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(content)
        
        local_url = f"/nav_backgrounds/{filename}"
        # 更新配置
        nav_service.update_settings({
            "background_url": local_url,
            "wallpaper_mode": "custom"
        })
        print(f"[Navigation] Successfully saved remote background to: {local_url}")
        return {"url": local_url}
    except Exception as e:
        print(f"[Navigation] Final save error: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

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
    icon = category.icon
    if icon and icon.startswith(("http://", "https://")):
        local_path = await download_and_cache_icon(icon)
        if local_path:
            icon = local_path
            
    cat_obj = nav_service.add_category(category.name, icon, category.order)
    return cat_obj

@router.put("/categories/{cat_id}")
async def update_category(cat_id: int, category: CategoryCreate):
    icon = category.icon
    if icon and icon.startswith(("http://", "https://")):
        local_path = await download_and_cache_icon(icon)
        if local_path:
            icon = local_path
            
    nav_service.update_category(cat_id, category.name, icon, category.order)
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
    # 自动本地化远程图标 (智能抓取)
    site_data = site.dict()
    icon = site_data.get("icon")
    if icon and icon.startswith(("http://", "https://")):
        local_path = await get_and_cache_favicon(icon)
        if local_path:
            site_data["icon"] = local_path
            
    return nav_service.add_site(site_data)

@router.put("/{site_id}")
async def update_site(site_id: int, site: SiteNavUpdate):
    # 自动本地化远程图标 (智能抓取)
    site_data = site.dict(exclude_unset=True)
    icon = site_data.get("icon")
    if icon and icon.startswith(("http://", "https://")):
        local_path = await get_and_cache_favicon(icon)
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
            
            # 3. 写入背景目录
            if os.path.exists(BG_DIR):
                for file in os.listdir(BG_DIR):
                    fpath = os.path.join(BG_DIR, file)
                    if os.path.isfile(fpath):
                        zf.write(fpath, os.path.join("nav_backgrounds", file))
        
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
            
            # 2. 搬运背景
            zip_bgs_path = os.path.join(temp_dir, "nav_backgrounds")
            if os.path.exists(zip_bgs_path):
                for fname in os.listdir(zip_bgs_path):
                    shutil.copy2(os.path.join(zip_bgs_path, fname), os.path.join(BG_DIR, fname))
            
            # 3. 覆盖配置 (使用 save_nav_data 以触发自动备份和标准化)
            nav_json_path = os.path.join(temp_dir, "navigation.json")
            with open(nav_json_path, "r", encoding="utf-8") as f:
                raw_nav_data = json.load(f)
            
            # 标准化数据
            final_nav_data = nav_service.normalize_nav_data(raw_nav_data)
            
            # --- 自动本地化导入的远程图标 ---
            # 处理分类图标
            for cat in final_nav_data.get("categories", []):
                icon = cat.get("icon")
                if icon and icon.startswith(("http://", "https://")):
                    local_path = await download_and_cache_icon(icon)
                    if local_path:
                        cat["icon"] = local_path
            
            # 处理站点图标
            for site in final_nav_data.get("sites", []):
                icon = site.get("icon")
                if icon and icon.startswith(("http://", "https://")):
                    local_path = await download_and_cache_icon(icon)
                    if local_path:
                        site["icon"] = local_path
            
            nav_service.save_nav_data(final_nav_data)
            
        nav_service.cleanup_orphaned_icons() 
        nav_service.cleanup_orphaned_backgrounds()
        return {"message": "全量恢复成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ==========================================
# 增强型图标抓取
# ==========================================

# 简单的内存缓存: { "key": { "date": "2023-10-27", "data": {...} } }
BING_CACHE = {}

@router.get("/bing-wallpaper")
async def get_bing_wallpaper(
    index: int = 0, 
    mkt: str = "zh-CN",
    resolution: str = "1920x1080"
):
    """获取必应每日壁纸及其元数据（带服务端缓存）"""
    try:
        # 1. 生成缓存 Key 和当前日期
        cache_key = f"{mkt}_{index}_{resolution}"
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 2. 检查缓存
        if cache_key in BING_CACHE:
            cached = BING_CACHE[cache_key]
            # 只有当缓存数据的日期是"今天"时才使用，确保跨天自动更新
            if cached.get("date") == today_str:
                return cached.get("data")

        # 3. 缓存未命中或过期，请求 Bing API
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx={index}&n=1&mkt={mkt}"
        async with get_async_client(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if "images" in data and len(data["images"]) > 0:
                    image = data["images"][0]
                    # 构建完整图片 URL
                    base_url = f"https://www.bing.com{image['urlbase']}_{resolution}.jpg"
                    
                    result_data = {
                        "url": base_url,
                        "title": image.get("title", ""),
                        "copyright": image.get("copyright", ""),
                        "copyrightlink": image.get("copyrightlink", "")
                    }

                    # 4. 写入缓存
                    BING_CACHE[cache_key] = {
                        "date": today_str,
                        "data": result_data
                    }
                    
                    return result_data

    except Exception as e:
        print(f"Fetch bing error: {e}")
    
    return {"error": "Failed to fetch"}

async def get_and_cache_favicon(url: str) -> Optional[str]:
    """抓取网页图标并自动本地化"""
    if not url.startswith(("http://", "https://")):
        url = 'https://' + url
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    remote_icon_url = None
    try:
        async with get_async_client(timeout=10.0, headers=headers, use_proxy=True) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                # 如果返回的是图片，直接用
                ctype = resp.headers.get("content-type", "").lower()
                if "image/" in ctype:
                    return await download_and_cache_icon(url)

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
        return await download_and_cache_icon(remote_icon_url)
            
    except Exception:
        try:
            parsed = urlparse(url)
            remote_icon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
            return await download_and_cache_icon(remote_icon_url)
        except:
            return None

@router.get("/fetch-icon")
async def fetch_icon(url: str = Query(...)):
    """抓取网页图标并自动本地化"""
    local_path = await get_and_cache_favicon(url)
    return {"icon": local_path or url}

# ==========================================
# 分类管理 API
# ==========================================