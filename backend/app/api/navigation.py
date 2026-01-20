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
from urllib.parse import urljoin, urlparse

from app.services import navigation_service as nav_service
from app.schemas.navigation import (
    SiteNavCreate, SiteNavUpdate, SiteNavResponse,
    CategoryCreate, CategoryResponse
)

router = APIRouter()

ICON_DIR = "/app/data/nav_icons"
os.makedirs(ICON_DIR, exist_ok=True)

# --- 导入导出 (全量 ZIP 版) ---

@router.get("/export")
async def export_navigation():
    # 创建一个临时 ZIP 文件
    temp_zip = tempfile.mktemp(suffix=".zip")
    
    try:
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. 写入配置文件
            if os.path.exists(nav_service.NAV_FILE):
                zf.write(nav_service.NAV_FILE, "navigation.json")
            else:
                # 如果文件还没创建，生成一份默认的存进去
                default_data = json.dumps(nav_service.DEFAULT_NAV).encode('utf-8')
                zf.writestr("navigation.json", default_data)
            
            # 2. 写入所有图标文件
            if os.path.exists(ICON_DIR):
                for root, dirs, files in os.walk(ICON_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 在 ZIP 中的路径为 nav_icons/filename
                        zf.write(file_path, os.path.join("nav_icons", file))
        
        return FileResponse(
            path=temp_zip, 
            filename=f"embylens_backup_{uuid.uuid4().hex[:8]}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打包备份失败: {str(e)}")

@router.post("/import")
async def import_navigation(file: UploadFile = File(...)):
    # 创建临时目录解压
    temp_dir = tempfile.mkdtemp()
    temp_zip = os.path.join(temp_dir, "upload.zip")
    
    try:
        with open(temp_zip, "wb") as f:
            f.write(await file.read())
            
        with zipfile.ZipFile(temp_zip, 'r') as zf:
            # 校验是否存在 navigation.json
            if "navigation.json" not in zf.namelist():
                raise HTTPException(status_code=400, detail="备份包中缺少 navigation.json")
            
            # 1. 恢复图标
            # 我们先清理掉旧的图标，或者直接覆盖合并
            # 为了数据一致性，建议先解压到临时路径再搬运
            zf.extractall(temp_dir)
            
            # 2. 搬运图标文件
            zip_icons_path = os.path.join(temp_dir, "nav_icons")
            if os.path.exists(zip_icons_path):
                for file_name in os.listdir(zip_icons_path):
                    src = os.path.join(zip_icons_path, file_name)
                    dst = os.path.join(ICON_DIR, file_name)
                    shutil.copy2(src, dst)
            
            # 3. 覆盖配置文件
            src_json = os.path.join(temp_dir, "navigation.json")
            shutil.copy2(src_json, nav_service.NAV_FILE)
            
        return {"message": "全量备份导入成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

# --- 工具函数：下载并缓存图标 (保持不变) ---
async def download_and_cache_icon(url: str) -> Optional[str]:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers, verify=False) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                ext = ".png"
                content_type = resp.headers.get("content-type", "").lower()
                if "image/svg" in content_type: ext = ".svg"
                elif "image/x-icon" in content_type: ext = ".ico"
                elif "image/webp" in content_type: ext = ".webp"
                elif "image/jpeg" in content_type: ext = ".jpg"
                filename = f"{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(ICON_DIR, filename)
                with open(filepath, "wb") as f: f.write(resp.content)
                return f"/nav_icons/{filename}"
    except Exception: pass
    return None

# --- 分类与站点 API (调用 nav_service，保持不变) ---
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

@router.get("/fetch-icon")
async def fetch_icon(url: str = Query(...)):
    if not url.startswith(('http://', 'https://')): url = 'https://' + url
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers, verify=False) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                html = resp.text
                links = re.findall(r'<link\s+[^>]*>', html, re.I)
                potential_icons = []
                for link in links:
                    if re.search(r'rel=[\"\"](.*?icon.*?)[\"\"]', link, re.I):
                        href_match = re.search(r'href=[\"\"](.*?)[\"\"]', link, re.I)
                        if href_match: potential_icons.append(href_match.group(1))
                if potential_icons:
                    best_icon = potential_icons[0]
                    for icon in potential_icons:
                        if any(ext in icon.lower() for ext in ['.png', '.svg', '.webp']):
                            best_icon = icon
                            break
                    remote_icon_url = urljoin(url, best_icon)
                else:
                    logo_match = re.search(r'<img[^>]*src=[\"\"]([^\"\"]*(?:logo|icon)[^\"\"]*)[\"\"]', html, re.I)
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
