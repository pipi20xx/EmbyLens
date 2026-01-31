from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Response
from typing import List, Optional
from datetime import datetime
from app.services import bookmark_service as service
from app.schemas.bookmark import BookmarkCreate, BookmarkUpdate, BookmarkResponse

router = APIRouter()

# 使用标准的 / 路径，确保匹配稳定
@router.get("/", response_model=List[BookmarkResponse])
async def list_bookmarks(as_tree: bool = Query(True)):
    return service.list_bookmarks(as_tree=as_tree)

@router.post("/", response_model=BookmarkResponse)
async def create_bookmark(bookmark: BookmarkCreate):
    return service.add_bookmark(bookmark.dict())

@router.put("/{bm_id}")
async def update_bookmark(bm_id: str, bookmark: BookmarkUpdate):
    success = service.update_bookmark(bm_id, bookmark.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"message": "Updated"}

@router.delete("/{bm_id}")
async def delete_bookmark(bm_id: str):
    success = service.delete_bookmark(bm_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"message": "Deleted"}

@router.delete("/")
async def clear_bookmarks_root():
    service.clear_bookmarks()
    return {"message": "All bookmarks cleared"}

@router.get("/export")
async def export_bookmarks():
    html_content = service.export_bookmarks_to_html()
    filename = f"lens_bookmarks_{datetime.now().strftime('%Y%m%d')}.html"
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.post("/reorder")
async def reorder_bookmarks(payload: dict):
    ordered_ids = payload.get("ordered_ids", [])
    parent_id = payload.get("parent_id")
    service.reorder_bookmarks(ordered_ids, parent_id)
    return {"message": "Reordered"}

@router.post("/import-html")
async def import_bookmarks_html(file: UploadFile = File(...)):
    if not file.filename.endswith(('.html', '.htm')):
        raise HTTPException(status_code=400, detail="请上传 HTML 格式的书签文件")
    
    content = await file.read()
    html_text = ""
    for enc in ['utf-8-sig', 'utf-8', 'gbk', 'iso-8859-1']:
        try:
            html_text = content.decode(enc)
            break
        except:
            continue
            
    if not html_text:
        raise HTTPException(status_code=400, detail="无法解析文件编码")
            
    count = service.import_from_html(html_text)
    return {"message": f"成功导入 {count} 个项目", "count": count}