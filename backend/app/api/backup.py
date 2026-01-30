from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from app.core.config_manager import get_config, save_config
from app.services.backup_service import BackupService
from app.schemas.backup import BackupTaskSchema, BackupHistorySchema
from app.models.backup import BackupHistory
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid
import os
import asyncio

router = APIRouter()

@router.get("/tasks", response_model=List[BackupTaskSchema])
async def get_tasks():
    config = get_config()
    return config.get("backup_tasks", [])

@router.post("/tasks")
async def add_task(task: BackupTaskSchema):
    config = get_config()
    tasks = config.get("backup_tasks", [])
    
    new_task = task.dict()
    if not new_task.get("id"):
        new_task["id"] = str(uuid.uuid4())[:8]
    
    tasks.append(new_task)
    config["backup_tasks"] = tasks
    save_config(config)
    
    await BackupService.reload_tasks()
    return new_task

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, task: BackupTaskSchema):
    config = get_config()
    tasks = config.get("backup_tasks", [])
    
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            updated_task = task.dict()
            updated_task["id"] = task_id
            tasks[i] = updated_task
            config["backup_tasks"] = tasks
            save_config(config)
            await BackupService.reload_tasks()
            return updated_task
            
    raise HTTPException(status_code=404, detail="Task not found")

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    config = get_config()
    tasks = config.get("backup_tasks", [])
    
    new_tasks = [t for t in tasks if t.get("id") != task_id]
    if len(new_tasks) == len(tasks):
        raise HTTPException(status_code=404, detail="Task not found")
        
    config["backup_tasks"] = new_tasks
    save_config(config)
    await BackupService.reload_tasks()
    return {"message": "Task deleted"}

@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str, background_tasks: BackgroundTasks):
    # 手动触发执行
    background_tasks.add_task(BackupService.run_backup_task, task_id)
    return {"message": "Backup task started in background"}

@router.post("/history/{history_id}/restore")
async def restore_backup(history_id: int, background_tasks: BackgroundTasks, clear_dst: bool = False):
    # 改为后台执行，立即返回
    background_tasks.add_task(BackupService.run_restore_task, history_id, clear_dst)
    return {"message": "还原任务已在后台启动"}

@router.get("/history", response_model=List[BackupHistorySchema])
async def get_history(task_id: Optional[str] = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(BackupHistory)
    if task_id:
        query = query.where(BackupHistory.task_id == task_id)
    
    result = await db.execute(
        query.order_by(desc(BackupHistory.start_time)).limit(limit)
    )
    return result.scalars().all()

@router.get("/path-browser")
async def path_browser(path: str = "/"):
    """
    智能路径浏览器：获取指定目录下的文件和文件夹
    只读取元数据，不读取内容，适合网盘
    """
    def scan_path():
        if not os.path.exists(path):
            return {"current_path": path, "items": [], "error": "Path does not exist"}
        
        items = []
        try:
            for entry in os.scandir(path):
                try:
                    is_dir = entry.is_dir()
                    items.append({
                        "name": entry.name,
                        "is_dir": is_dir,
                        "path": entry.path,
                        "size": 0 if is_dir else entry.stat().st_size
                    })
                except:
                    continue
            
            # 排序：文件夹在前，文件名在后
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            return {"current_path": path, "items": items}
        except Exception as e:
            return {"error": str(e)}

    # 在线程池中执行磁盘扫描
    res = await asyncio.to_thread(scan_path)
    if "error" in res and res["error"] != "Path does not exist":
        raise HTTPException(status_code=500, detail=res["error"])
    return res