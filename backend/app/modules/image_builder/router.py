from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.session import get_db
from . import schemas, models, service

router = APIRouter()
Service = service.ImageBuilderService

# --- Project Endpoints ---
@router.get("/projects", response_model=List[schemas.Project])
async def get_projects(db: AsyncSession = Depends(get_db)):
    return await Service.get_projects(db)

@router.post("/projects", response_model=schemas.Project)
async def create_project(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_db)):
    return await Service.create_project(db, project)

@router.get("/projects/{project_id}", response_model=schemas.Project)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await Service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/projects/{project_id}", response_model=schemas.Project)
async def update_project(project_id: str, project_in: schemas.ProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await Service.update_project(db, project_id, project_in)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    success = await Service.delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success"}

# --- Registry Endpoints ---
@router.get("/registries", response_model=List[schemas.Registry])
async def get_registries(db: AsyncSession = Depends(get_db)):
    return await Service.get_registries(db)

@router.post("/registries", response_model=schemas.Registry)
async def create_registry(registry: schemas.RegistryCreate, db: AsyncSession = Depends(get_db)):
    return await Service.create_registry(db, registry)

@router.put("/registries/{registry_id}", response_model=schemas.Registry)
async def update_registry(registry_id: str, registry_in: schemas.RegistryUpdate, db: AsyncSession = Depends(get_db)):
    registry = await Service.update_registry(db, registry_id, registry_in)
    if not registry: raise HTTPException(status_code=404, detail="Registry not found")
    return registry

@router.delete("/registries/{registry_id}")
async def delete_registry(registry_id: str, db: AsyncSession = Depends(get_db)):
    success = await Service.delete_registry(db, registry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Registry not found")
    return {"status": "success"}

@router.post("/registries/{registry_id}/test")
async def test_registry(registry_id: str, db: AsyncSession = Depends(get_db)):
    return await Service.test_registry(db, registry_id)

# --- Credential Endpoints ---
@router.get("/credentials", response_model=List[schemas.Credential])
async def get_credentials(db: AsyncSession = Depends(get_db)):
    return await Service.get_credentials(db)

@router.post("/credentials", response_model=schemas.Credential)
async def create_credential(cred: schemas.CredentialCreate, db: AsyncSession = Depends(get_db)):
    return await Service.create_credential(db, cred)

@router.put("/credentials/{cred_id}", response_model=schemas.Credential)
async def update_credential(cred_id: str, cred_in: schemas.CredentialUpdate, db: AsyncSession = Depends(get_db)):
    cred = await Service.update_credential(db, cred_id, cred_in)
    if not cred: raise HTTPException(status_code=404, detail="Credential not found")
    return cred

@router.delete("/credentials/{cred_id}")
async def delete_credential(cred_id: str, db: AsyncSession = Depends(get_db)):
    success = await Service.delete_credential(db, cred_id)
    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"status": "success"}

# --- Proxy Endpoints ---
@router.get("/proxies", response_model=List[schemas.Proxy])
async def get_proxies(db: AsyncSession = Depends(get_db)):
    return await Service.get_proxies(db)

@router.post("/proxies", response_model=schemas.Proxy)
async def create_proxy(proxy: schemas.ProxyCreate, db: AsyncSession = Depends(get_db)):
    return await Service.create_proxy(db, proxy)

@router.put("/proxies/{proxy_id}", response_model=schemas.Proxy)
async def update_proxy(proxy_id: str, proxy_in: schemas.ProxyUpdate, db: AsyncSession = Depends(get_db)):
    proxy = await Service.update_proxy(db, proxy_id, proxy_in)
    if not proxy: raise HTTPException(status_code=404, detail="Proxy not found")
    return proxy

@router.delete("/proxies/{proxy_id}")
async def delete_proxy(proxy_id: str, db: AsyncSession = Depends(get_db)):
    success = await Service.delete_proxy(db, proxy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return {"status": "success"}

@router.delete("/tasks")
async def delete_all_task_logs(db: AsyncSession = Depends(get_db)):
    await Service.delete_all_task_logs(db)
    return {"status": "success"}

@router.get("/system-info")
async def get_system_info(host_id: str):
    return await Service.get_system_info(host_id)

@router.post("/setup-env")
async def setup_env(host_id: str = Body(..., embed=True), proxy_id: Optional[str] = Body(None, embed=True)):
    return await Service.setup_buildx_env(host_id, proxy_id)

# --- Task Endpoints ---
@router.post("/projects/{project_id}/build")
async def build_project(project_id: str, req: schemas.BuildRequest, db: AsyncSession = Depends(get_db)):
    task_id = await Service.start_build_task(db, project_id, req.tag)
    return {"task_id": task_id}

@router.get("/projects/{project_id}/tasks", response_model=List[schemas.TaskLog])
async def get_task_logs(project_id: str, db: AsyncSession = Depends(get_db)):
    return await Service.get_task_logs(db, project_id)

@router.get("/tasks/{task_id}/log")
async def get_task_log_content(task_id: str):
    log_path = service.BUILD_LOG_DIR / f"{task_id}.log"
    if not log_path.exists():
        return {"content": "Log file not found."}
    with open(log_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@router.delete("/tasks/{task_id}")
async def delete_task_log(task_id: str, db: AsyncSession = Depends(get_db)):
    await Service.delete_task_log(db, task_id)
    return {"status": "success"}
