from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.core.config_manager import get_config, save_config
from app.services.docker_service import DockerService
from app.utils.logger import logger, audit_log
import uuid
import time

router = APIRouter()

class DockerHostConfig(BaseModel):
    id: Optional[str] = None
    name: str
    type: str # 'local', 'ssh', or 'tcp'
    ssh_host: Optional[str] = None
    ssh_port: Optional[int] = 22
    ssh_user: Optional[str] = "root"
    ssh_pass: Optional[str] = None
    use_tls: Optional[bool] = False
    base_url: Optional[str] = None
    compose_scan_paths: Optional[str] = "" # 新增：逗号分隔的扫描路径

@router.get("/hosts")
async def get_hosts():
    config = get_config()
    return config.get("docker_hosts", [])

@router.post("/hosts")
async def add_host(host: DockerHostConfig):
    start_time = time.time()
    config = get_config()
    hosts = config.get("docker_hosts", [])
    
    new_host = host.dict()
    if not new_host.get("id"):
        new_host["id"] = str(uuid.uuid4())
    
    hosts.append(new_host)
    config["docker_hosts"] = hosts
    save_config(config)
    
    audit_log("Docker Host Added", (time.time() - start_time) * 1000, [f"Name: {new_host['name']}"])
    return new_host

@router.put("/hosts/{host_id}")
async def update_host(host_id: str, host: DockerHostConfig):
    config = get_config()
    hosts = config.get("docker_hosts", [])
    
    for i, h in enumerate(hosts):
        if h.get("id") == host_id:
            updated_host = host.dict()
            updated_host["id"] = host_id
            hosts[i] = updated_host
            config["docker_hosts"] = hosts
            save_config(config)
            return updated_host
            
    raise HTTPException(status_code=404, detail="Host not found")

@router.delete("/hosts/{host_id}")
async def delete_host(host_id: str):
    start_time = time.time()
    config = get_config()
    hosts = config.get("docker_hosts", [])
    
    new_hosts = [h for h in hosts if h.get("id") != host_id]
    if len(new_hosts) == len(hosts):
        raise HTTPException(status_code=404, detail="Host not found")
        
    config["docker_hosts"] = new_hosts
    save_config(config)
    
    audit_log("Docker Host Deleted", (time.time() - start_time) * 1000, [f"ID: {host_id}"])
    return {"message": "Host deleted"}

def get_docker_service(host_id: str):
    config = get_config()
    hosts = config.get("docker_hosts", [])
    host_config = next((h for h in hosts if h.get("id") == host_id), None)
    
    if not host_config:
        raise HTTPException(status_code=404, detail="Docker host not configured")
    
    return DockerService(host_config)

@router.get("/{host_id}/containers")
async def list_containers(host_id: str):
    service = get_docker_service(host_id)
    return service.list_containers()

@router.post("/{host_id}/containers/{container_id}/action")
async def container_action(host_id: str, container_id: str, action: str = Body(..., embed=True)):
    start_time = time.time()
    logger.info(f"🚀 [Docker] 收到容器操作请求: 动作={action}, 容器ID={container_id}, 主机={host_id}")
    service = get_docker_service(host_id)
    success = service.container_action(container_id, action)
    
    if not success:
        logger.error(f"❌ [Docker] 容器操作失败: {action} -> {container_id}")
        raise HTTPException(status_code=500, detail=f"Failed to perform action {action}")
    
    process_time = (time.time() - start_time) * 1000
    logger.info(f"✅ [Docker] 容器操作成功: {action} (耗时 {process_time:.1f}ms)")
    audit_log(f"Docker Action: {action}", process_time, [
        f"Host: {host_id}",
        f"Container: {container_id}"
    ])
    
    return {"message": f"Action {action} performed successfully"}

@router.get("/{host_id}/containers/{container_id}/logs")
async def get_container_logs(host_id: str, container_id: str, tail: int = 100):
    logger.info(f"📜 [Docker] 正在获取容器日志: {container_id} (tail={tail})")
    service = get_docker_service(host_id)
    logs = service.get_container_logs(container_id, tail)
    return {"logs": logs}

@router.post("/{host_id}/test")
async def test_connection(host_id: str):
    logger.info(f"🔍 [Docker] 正在测试主机连接: {host_id}")
    service = get_docker_service(host_id)
    is_ok = service.test_connection()
    if is_ok:
        logger.info(f"✨ [Docker] 主机连接测试成功: {host_id}")
    else:
        logger.error(f"💔 [Docker] 主机连接测试失败: {host_id}")
    return {"status": "ok" if is_ok else "error"}

@router.get("/container-settings")
async def get_container_settings():
    config = get_config()
    return config.get("docker_container_settings", {})

@router.post("/container-settings/{container_name}")
async def save_container_settings(container_name: str, settings: Dict[str, Any] = Body(...)):
    config = get_config()
    all_settings = config.get("docker_container_settings", {})
    all_settings[container_name] = settings
    config["docker_container_settings"] = all_settings
    save_config(config)
    return {"message": "Settings saved"}