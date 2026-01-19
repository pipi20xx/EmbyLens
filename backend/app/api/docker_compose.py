from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import shutil
import subprocess
import json
import time
from app.utils.logger import logger, audit_log
from app.core.config_manager import get_config
from app.services.docker_service import DockerService

router = APIRouter()

COMPOSE_DIR = "data/compose"

class ComposeProject(BaseModel):
    name: str
    content: str

def get_docker_service(host_id: str):
    config = get_config()
    hosts = config.get("docker_hosts", [])
    host_config = next((h for h in hosts if h.get("id") == host_id), None)
    
    if not host_config:
        raise HTTPException(status_code=404, detail="Docker host not configured")
    
    return DockerService(host_config)

@router.get("/{host_id}/ls")
async def list_directory(host_id: str, path: str = "/"):
    """浏览远程或本地主机的文件夹"""
    service = get_docker_service(host_id)
    # 使用 ls -F 命令来区分文件夹和文件，文件夹末尾会有 /
    cmd = f"ls -F '{path}'"
    res = service.exec_command(cmd)
    
    if not res["success"]:
        # 尝试默认路径
        if path != "/":
            return await list_directory(host_id, "/")
        raise HTTPException(status_code=500, detail=res["stderr"])

    items = []
    lines = res["stdout"].strip().split('\n')
    for line in lines:
        if not line: continue
        is_dir = line.endswith('/')
        name = line.rstrip('/')
        if is_dir:
            items.append({
                "name": name,
                "path": os.path.join(path, name),
                "is_dir": True
            })
    
    # 按名称排序，文件夹优先
    items.sort(key=lambda x: (not x["is_dir"], x["name"]))
    return {"current_path": path, "items": items}

@router.get("/{host_id}/projects")
async def list_projects(host_id: str):
    service = get_docker_service(host_id)
    projects = []
    managed_paths = set()
    
    # 1. 探测已运行的项目
    detect_commands = ["docker compose ls --all --format json", "docker-compose ls --all --format json"]
    for cmd in detect_commands:
        res = service.exec_command(cmd)
        if res["success"] and res["stdout"].strip():
            try:
                detected_projects = json.loads(res["stdout"])
                for p in detected_projects:
                    name = p.get("Name") or p.get("Project")
                    config_files = p.get("ConfigFiles") or p.get("ConfigPath")
                    if name and config_files:
                        projects.append({
                            "name": name,
                            "path": os.path.dirname(config_files),
                            "config_file": config_files,
                            "type": "detected",
                            "status": p.get("Status")
                        })
                        managed_paths.add(config_files)
                break
            except: continue

    # 2. 扫描指定路径
    scan_paths_str = service.host_config.get("compose_scan_paths", "")
    if scan_paths_str:
        paths = [p.strip() for p in scan_paths_str.split(",") if p.strip()]
        for base_path in paths:
            find_cmd = f"find {base_path} -maxdepth 4 \( -name 'docker-compose.yml' -o -name 'docker-compose.yaml' \)"
            res = service.exec_command(find_cmd)
            if res["success"] and res["stdout"].strip():
                found_files = res["stdout"].strip().split("\n")
                for file_path in found_files:
                    if not file_path or file_path in managed_paths: continue
                    project_dir = os.path.dirname(file_path)
                    projects.append({
                        "name": os.path.basename(project_dir),
                        "path": project_dir,
                        "config_file": file_path,
                        "type": "scanned",
                        "status": "exited"
                    })
                    managed_paths.add(file_path)

    # 3. 本置项目兜底 (仅本地主机)
    if service.host_config.get("type") == "local" and os.path.exists(COMPOSE_DIR):
        for d in os.listdir(COMPOSE_DIR):
            path = os.path.join(COMPOSE_DIR, d)
            cfg = os.path.join(path, "docker-compose.yml")
            if os.path.isdir(path) and cfg not in managed_paths:
                projects.append({
                    "name": d, "path": path, "config_file": cfg, "type": "internal", "status": "unknown"
                })
    
    return projects

@router.get("/{host_id}/projects/{name}")
async def get_project(host_id: str, name: str, path: Optional[str] = None):
    service = get_docker_service(host_id)
    if not path and service.host_config.get("type") == "local":
        path = os.path.join(COMPOSE_DIR, name, "docker-compose.yml")
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    content = service.read_file(path)
    if not content:
        raise HTTPException(status_code=404, detail="File not found")
    return {"name": name, "content": content, "path": path}

@router.post("/{host_id}/projects")
async def save_project(host_id: str, project: ComposeProject, path: Optional[str] = None):
    service = get_docker_service(host_id)
    if not path:
        if service.host_config.get("type") == "local":
            path = os.path.join(COMPOSE_DIR, project.name, "docker-compose.yml")
        else:
            path = f"/opt/docker-compose/{project.name}/docker-compose.yml"
    if service.write_file(path, project.content):
        return {"message": "Saved", "path": path}
    raise HTTPException(status_code=500, detail="Save failed")

@router.post("/{host_id}/projects/{name}/action")
async def project_action(host_id: str, name: str, action: str = Body(..., embed=True), path: Optional[str] = Body(None, embed=True)):
    service = get_docker_service(host_id)
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    cmd_map = {
        "up": f"docker compose -f {path} up -d",
        "down": f"docker compose -f {path} down",
        "pull": f"docker compose -f {path} pull",
        "restart": f"docker compose -f {path} restart"
    }
    res = service.exec_command(cmd_map[action], cwd=os.path.dirname(path))
    return {"success": res["success"], "stdout": res["stdout"], "stderr": res["stderr"]}

@router.delete("/{host_id}/projects/{name}")
async def delete_project(host_id: str, name: str, path: Optional[str] = None):
    return {"message": "Removed from view"}
