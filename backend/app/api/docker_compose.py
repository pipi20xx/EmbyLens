from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import shutil
import subprocess
import json
import time
from app.utils.logger import logger, audit_log
from app.core.config_manager import get_config, save_config
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
    """浏览远程或本地主机的目录内容"""
    service = get_docker_service(host_id)
    # 使用 ls -p 参数，文件夹后会跟 /
    cmd = f"ls -p '{path}'"
    res = service.exec_command(cmd, log_error=False)
    
    if not res["success"]:
        if path != "/":
            return await list_directory(host_id, "/")
        raise HTTPException(status_code=500, detail=res["stderr"])

    items = []
    lines = res["stdout"].strip().split('\n')
    for line in lines:
        if not line: continue
        is_dir = line.endswith('/')
        name = line.rstrip('/')
        items.append({
            "name": name,
            "path": os.path.join(path, name),
            "is_dir": is_dir
        })
    
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return {"current_path": path, "items": items}

@router.get("/{host_id}/projects")
async def list_projects(host_id: str):
    service = get_docker_service(host_id)
    projects = []
    managed_paths = set()
    
    # 1. 尝试通过 docker compose ls 探测已运行的项目
    detect_commands = ["docker compose ls --all --format json", "docker-compose ls --all --format json"]
    for cmd in detect_commands:
        res = service.exec_command(cmd, log_error=False)
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

    # 2. 根据用户配置的扫描路径进行深度搜索
    scan_paths_str = service.host_config.get("compose_scan_paths", "")
    if scan_paths_str:
        paths = [p.strip() for p in scan_paths_str.split(",") if p.strip()]
        for base_path in paths:
            # 静默检查路径是否存在
            check_cmd = f"[ -d '{base_path}' ] && echo 'ok'"
            if service.exec_command(check_cmd, log_error=False)["stdout"].strip() != "ok":
                continue

            find_cmd = f"find {base_path} -maxdepth 4 \( -name 'docker-compose.yml' -o -name 'docker-compose.yaml' \)"
            res = service.exec_command(find_cmd, log_error=False)
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

    # 3. 本地内置项目
    if service.host_config.get("type") == "local" and os.path.exists(COMPOSE_DIR):
        for d in os.listdir(COMPOSE_DIR):
            path = os.path.join(COMPOSE_DIR, d)
            cfg = os.path.join(path, "docker-compose.yml")
            if os.path.isdir(path) and cfg not in managed_paths:
                projects.append({"name": d, "path": path, "config_file": cfg, "type": "internal", "status": "unknown"})
    
    return projects

@router.get("/{host_id}/projects/{name}")
async def get_project(host_id: str, name: str, path: Optional[str] = None):
    service = get_docker_service(host_id)
    if not path and service.host_config.get("type") == "local":
        path = os.path.join(COMPOSE_DIR, name, "docker-compose.yml")
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    content = service.read_file(path)
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

@router.post("/{host_id}/chmod")
async def chmod_path(host_id: str, path: str = Body(..., embed=True), mode: Optional[str] = Body(None, embed=True), 
                     owner: Optional[str] = Body(None, embed=True), group: Optional[str] = Body(None, embed=True), 
                     recursive: bool = Body(False, embed=True)):
    service = get_docker_service(host_id)
    rec_flag = "-R " if recursive else ""
    if mode:
        service.exec_command(f"chmod {rec_flag}{mode} '{path}'")
    if owner or group:
        target = f"{owner or ''}:{group or ''}".strip(":")
        service.exec_command(f"chown {rec_flag}{target} '{path}'")
    return {"message": "Success"}

@router.delete("/{host_id}/projects/{name}")
async def delete_project(host_id: str, name: str, path: Optional[str] = None, delete_files: bool = False):
    config = get_config()
    hosts = config.get("docker_hosts", [])
    host_match = next((h for h in hosts if h.get("id") == host_id), None)
    service = get_docker_service(host_id)
    
    if delete_files and path:
        project_dir = os.path.dirname(path).rstrip('/')
        if len(project_dir) < 5 or project_dir in ["/", "/root", "/home", "/etc", "/var"]:
            raise HTTPException(status_code=400, detail="Security Limit: Cannot delete system directories")
        
        service.exec_command(f"rm -rf '{project_dir}'")
        
        if host_match and "compose_scan_paths" in host_match:
            paths = [p.strip().rstrip('/') for p in host_match["compose_scan_paths"].split(",") if p.strip()]
            if project_dir in paths:
                paths = [p for p in paths if p != project_dir]
                host_match["compose_scan_paths"] = ",".join(paths)
                save_config(config)

    return {"message": "Removed"}