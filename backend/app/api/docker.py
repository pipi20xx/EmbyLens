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

from fastapi import APIRouter, HTTPException, Depends, Body, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from typing import List, Dict, Any, Optional
import asyncio
import select

# ... (keep existing imports)

@router.websocket("/{host_id}/containers/{container_id}/exec")
async def container_exec(websocket: WebSocket, host_id: str, container_id: str, command: str = "/bin/bash"):
    await websocket.accept()
    
    try:
        service = get_docker_service(host_id)
        # 获取 Docker 交互式 Socket
        sock = service.get_container_socket(container_id, command)
        if not sock:
            await websocket.send_text("\r\n❌ 无法连接到容器终端 (可能不支持 " + command + ")\r\n")
            await websocket.close()
            return

        # 设置非阻塞模式 (兼容标准 socket 和 paramiko Channel)
        try:
            if hasattr(sock, 'setblocking'):
                sock.setblocking(False)
            elif hasattr(sock, 'settimeout'):
                sock.settimeout(0.0)
        except:
            pass

        async def socket_to_ws():
            try:
                while True:
                    await asyncio.sleep(0.02) # 稍微降低频率，防止 CPU 占用过高
                    
                    # 检查是否有数据可读
                    has_data = False
                    if hasattr(sock, 'recv_ready'): # Paramiko Channel
                        has_data = sock.recv_ready()
                    else: # Standard socket
                        r, _, _ = select.select([sock], [], [], 0.01)
                        has_data = bool(r)

                    if has_data:
                        data = sock.recv(4096)
                        if not data:
                            break
                        await websocket.send_bytes(data)
            except Exception as e:
                logger.error(f"Socket to WS error: {e}")
            finally:
                try:
                    await websocket.close()
                except:
                    pass

        read_task = asyncio.create_task(socket_to_ws())

        try:
            while True:
                # 接收前端输入
                data = await websocket.receive_text()
                # 写入 Docker Socket
                if hasattr(sock, 'sendall'):
                    sock.sendall(data.encode())
                else:
                    sock.send(data.encode())
        except (WebSocketDisconnect, ConnectionClosed):
            pass
        except Exception as e:
            logger.error(f"WS to Socket error: {e}")
        finally:
            read_task.cancel()
            try:
                sock.close()
            except:
                pass
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass

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

@router.post("/{host_id}/prune-images")
async def prune_images(host_id: str, dangling: bool = Body(True, embed=True), all_unused: bool = Body(False, embed=True)):
    """清理镜像"""
    service = get_docker_service(host_id)
    # 构建命令
    cmd = "docker image prune -f"
    if all_unused:
        cmd = "docker image prune -a -f"
    elif not dangling:
        return {"message": "No action taken", "stdout": ""}
        
    res = service.exec_command(cmd)
    return {"success": res["success"], "stdout": res["stdout"], "stderr": res["stderr"]}

@router.post("/{host_id}/prune-cache")
async def prune_cache(host_id: str):
    """清理构建缓存"""
    service = get_docker_service(host_id)
    res = service.exec_command("docker builder prune -f")
    return {"success": res["success"], "stdout": res["stdout"], "stderr": res["stderr"]}

import json
import os

class DaemonUpdate(BaseModel):
    config: Dict[str, Any]
    restart: bool = False

@router.get("/{host_id}/daemon-config")
async def get_daemon_config(host_id: str):
    """读取远程主机的 /etc/docker/daemon.json"""
    service = get_docker_service(host_id)
    content = service.read_file("/etc/docker/daemon.json")
    if not content:
        return {}
    try:
        return json.loads(content)
    except:
        return {"_raw": content}

@router.post("/{host_id}/daemon-config")
async def save_daemon_config(host_id: str, data: DaemonUpdate):
    """保存配置并备份"""
    service = get_docker_service(host_id)
    config = data.config
    restart = data.restart
    
    # 1. 读取旧配置用于备份
    old_content = service.read_file("/etc/docker/daemon.json")
    
    # 2. 本地备份
    if old_content:
        backup_dir = "data/backups/daemon_configs"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        with open(f"{backup_dir}/{host_id}_{timestamp}.json", "w") as f:
            f.write(old_content)
            
        # 3. 远程备份 (daemon.json.bak)
        service.exec_command("cp /etc/docker/daemon.json /etc/docker/daemon.json.bak")

    # 4. 写入新配置
    new_content = json.dumps(config, indent=4)
    if not service.write_file("/etc/docker/daemon.json", new_content):
        raise HTTPException(status_code=500, detail="写入文件失败，请检查 SSH 账户是否有 root 权限")

    # 5. 重启 Docker (如果勾选)
    restart_res = None
    if restart:
        # 使用 systemctl 重启，这是最标准的方式
        restart_res = service.exec_command("systemctl daemon-reload && systemctl restart docker")

    return {
        "message": "配置已保存并备份", 
        "restart_result": restart_res
    }

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