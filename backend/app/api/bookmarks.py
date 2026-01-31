from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Optional
from app.services import bookmark_service as service
from app.schemas.bookmark import BookmarkCreate, BookmarkUpdate, BookmarkResponse

router = APIRouter()

@router.get("", response_model=List[BookmarkResponse])
async def list_bookmarks(as_tree: bool = Query(True)):
    return service.list_bookmarks(as_tree=as_tree)

@router.post("", response_model=BookmarkResponse)
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
    print(f"[Bookmarks] Received file: {file.filename}, size: {len(content)} bytes")
    
    # 尝试多种编码
    html_text = ""
    for enc in ['utf-8-sig', 'utf-8', 'gbk', 'iso-8859-1']:
        try:
            html_text = content.decode(enc)
            print(f"[Bookmarks] Decoded using {enc}")
            break
        except UnicodeDecodeError:
            continue
            
    if not html_text:
        raise HTTPException(status_code=400, detail="无法识别的文件编码")
            
    count = service.import_from_html(html_text)
    print(f"[Bookmarks] Successfully imported {count} items")
    return {"message": f"成功导入 {count} 个项目", "count": count}