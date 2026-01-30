from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.core.config_manager import get_config, save_config
from app.services.docker_service import DockerService
from app.services.notification_service import NotificationService
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
    is_local: Optional[bool] = False # 新增：标记为 Lens 宿主机
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
    return await asyncio.to_thread(service.list_containers)

@router.get("/{host_id}/check-image-update")
async def check_single_image_update(host_id: str, image: str):
    """单镜像精准检测"""
    service = get_docker_service(host_id)
    info = await service.get_image_update_info(image)
    return {image: info}

@router.post("/{host_id}/containers/{container_id}/action")
async def container_action(host_id: str, container_id: str, action: str = Body(..., embed=True)):
    start_time = time.time()
    logger.info(f"🚀 [Docker] 收到容器操作请求: 动作={action}, 容器ID={container_id}, 主机={host_id}")
    service = get_docker_service(host_id)
    
    # 尝试获取容器名称，用于通知 (异步化)
    container_name = container_id
    try:
        if service.client:
            def get_name():
                return service.client.containers.get(container_id).name
            container_name = await asyncio.to_thread(get_name)
    except Exception:
        pass

    # 在线程池中执行耗时操作
    success = await asyncio.to_thread(service.container_action, container_id, action)
    
    if not success:
        logger.error(f"❌ [Docker] 容器操作失败: {action} -> {container_id}")
        raise HTTPException(status_code=500, detail=f"Failed to perform action {action}")
    
    process_time = (time.time() - start_time) * 1000
    logger.info(f"✅ [Docker] 容器操作成功: {action} (耗时 {process_time:.1f}ms)")
    
    # 发送通知
    config = get_config()
    hosts = config.get("docker_hosts", [])
    host_name = next((h.get("name") for h in hosts if h.get("id") == host_id), "Unknown Host")
    
    # 操作名称中文化
    action_map = {
        "start": "启动 (Start)",
        "stop": "停止 (Stop)",
        "restart": "重启 (Restart)",
        "remove": "删除 (Remove)",
        "recreate": "重构 (Recreate)"
    }
    display_action = action_map.get(action, action)

    asyncio.create_task(NotificationService.emit(
        event="docker.container_action",
        title="Docker 容器操作提醒",
        message=f"主机: {host_name}\n容器名称: {container_name}\n容器 ID: {container_id[:12]}\n操作: {display_action}\n结果: 成功"
    ))

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

async def run_cleanup_background(host_id: str, cmd: str, task_name: str):
    """在后台执行清理任务并发送通知"""
    logger.info(f"🧹 [Docker] 开始执行后台清理任务: {task_name} (Host: {host_id})")
    
    # 获取主机名用于通知
    config = get_config()
    hosts = config.get("docker_hosts", [])
    host_name = next((h.get("name") for h in hosts if h.get("id") == host_id), host_id)
    
    # 异步执行耗时命令
    def execute():
        service = get_docker_service(host_id)
        return service.exec_command(cmd)
    
    res = await asyncio.to_thread(execute)
    
    # 准备通知内容
    status = "成功" if res["success"] else "失败"
    message = f"主机: {host_name}\n任务: {task_name}\n状态: {status}\n\n"
    if res["stdout"]:
        message += f"输出详情:\n{res['stdout'][-500:]}" # 仅保留最后500字符
    if res["stderr"]:
        message += f"\n错误详情:\n{res['stderr']}"

    await NotificationService.emit(
        event="docker.cleanup",
        title=f"Docker {task_name}完成",
        message=message
    )
    logger.info(f"✨ [Docker] 后台清理任务完成: {task_name}")

@router.post("/{host_id}/prune-images")
async def prune_images(host_id: str, dangling: bool = Body(True, embed=True), all_unused: bool = Body(False, embed=True)):
    """清理镜像"""
    # 构建命令
    cmd = "docker image prune -f"
    if all_unused:
        cmd = "docker image prune -a -f"
    elif not dangling:
        return {"message": "未选择清理选项"}
        
    asyncio.create_task(run_cleanup_background(host_id, cmd, "镜像清理"))
    return {"message": "镜像清理任务已在后台启动，完成后将通过通知告知您"}

@router.post("/{host_id}/prune-cache")
async def prune_cache(host_id: str):
    """清理构建缓存"""
    asyncio.create_task(run_cleanup_background(host_id, "docker builder prune -f", "构建缓存清理"))
    return {"message": "构建缓存清理任务已在后台启动，完成后将通过通知告知您"}

@router.post("/{host_id}/prune-containers")
async def prune_containers(host_id: str):
    """清理停止的容器"""
    asyncio.create_task(run_cleanup_background(host_id, "docker container prune -f", "容器清理"))
    return {"message": "容器清理任务已在后台启动，完成后将通过通知告知您"}

@router.get("/{host_id}/system-info")
async def get_system_info(host_id: str):
    """检测远程主机的 Docker 环境信息"""
    service = get_docker_service(host_id)
    
    # 检测 Docker 版本
    docker_ver = service.exec_command("docker version --format '{{.Server.Version}}' 2>/dev/null || docker -v")
    # 检测 Docker Compose 版本
    compose_ver = service.exec_command("docker compose version --short 2>/dev/null || docker-compose version --short 2>/dev/null || docker-compose -v")
    # 检测 操作系统信息
    os_info = service.exec_command("uname -snrmo")
    # 检测 Docker 服务状态
    service_status = service.exec_command("systemctl is-active docker 2>/dev/null || echo 'unknown'")

    return {
        "docker": docker_ver["stdout"].strip() if docker_ver["success"] else "未安装",
        "compose": compose_ver["stdout"].strip() if compose_ver["success"] else "未安装",
        "os": os_info["stdout"].strip() if os_info["success"] else "未知",
        "status": service_status["stdout"].strip()
    }

@router.post("/{host_id}/install-env")
async def install_docker_env(host_id: str, use_mirror: bool = Body(True, embed=True), proxy: Optional[str] = Body(None, embed=True)):
    """一键安装 Docker 和 Docker Compose"""
    service = get_docker_service(host_id)
    
    # 构造代理前缀
    proxy_prefix = f"export http_proxy={proxy} && export https_proxy={proxy} && " if proxy else ""
    
    # 使用 Docker 官方安装脚本
    mirror_cmd = " --mirror Aliyun" if use_mirror else ""
    install_cmd = f"curl -fsSL https://get.docker.com | sh -s --{mirror_cmd}"
    
    setup_cmd = (
        f"{proxy_prefix}"
        f"{install_cmd} && "
        "systemctl enable docker && systemctl start docker"
    )
    
    logger.info(f"🛠️ [Docker] 开始在主机 {host_id} 上安装环境...")
    res = service.exec_command(setup_cmd)
    
    if res["success"]:
        logger.info(f"✨ [Docker] 主机 {host_id} 环境安装完成")
    else:
        logger.error(f"❌ [Docker] 主机 {host_id} 环境安装失败: {res['stderr']}")
    
    # 发送通知
    config = get_config()
    hosts = config.get("docker_hosts", [])
    host_name = next((h.get("name") for h in hosts if h.get("id") == host_id), host_id)
    
    asyncio.create_task(NotificationService.emit(
        event="docker.host_action",
        title="Docker 环境安装结果",
        message=f"主机: {host_name}\n状态: {'成功' if res['success'] else '失败'}\n{res['stderr'] if not res['success'] else ''}"
    ))
        
    return {
        "success": res["success"],
        "stdout": res["stdout"],
        "stderr": res["stderr"]
    }

@router.post("/{host_id}/service-action")
async def docker_service_action(host_id: str, action: str = Body(..., embed=True)):
    """控制 Docker 核心服务 (start, stop, restart)"""
    service = get_docker_service(host_id)
    
    # 构造 systemctl 命令
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    cmd = f"systemctl {action} docker"
    logger.info(f"⚙️ [Docker] 正在对主机 {host_id} 执行服务操作: {action}")
    res = service.exec_command(cmd)
    
    # 发送通知
    config = get_config()
    hosts = config.get("docker_hosts", [])
    host_name = next((h.get("name") for h in hosts if h.get("id") == host_id), host_id)
    
    asyncio.create_task(NotificationService.emit(
        event="docker.host_action",
        title="Docker 服务操作提醒",
        message=f"主机: {host_name}\n操作: {action}\n结果: {'成功' if res['success'] else '失败'}"
    ))

    return {
        "success": res["success"],
        "stdout": res["stdout"],
        "stderr": res["stderr"]
    }

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
        restart_res = service.exec_command("systemctl daemon-reload && systemctl restart docker")

    return {
        "message": "配置已保存并备份", 
        "restart_result": restart_res
    }

@router.get("/{host_id}/daemon-config/raw")
async def get_daemon_config_raw(host_id: str):
    """获取原始 daemon.json 文本"""
    service = get_docker_service(host_id)
    content = service.read_file("/etc/docker/daemon.json")
    return {"content": content or "{}"}

@router.post("/{host_id}/daemon-config/raw")
async def save_daemon_config_raw(host_id: str, data: Dict[str, Any] = Body(...)):
    """保存原始 daemon.json 文本"""
    host_id = host_id
    content = data.get("content")
    restart = data.get("restart", False)
    
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
        
    # 校验 JSON 格式
    try:
        json_obj = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 格式错误: {str(e)}")
        
    # 重用之前的保存逻辑 (会自动备份)
    return await save_daemon_config(host_id, DaemonUpdate(config=json_obj, restart=restart))

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

class DockerAutoUpdateSettings(BaseModel):
    enabled: bool
    type: str # 'cron' or 'interval'
    value: str

@router.get("/auto-update/settings")
async def get_auto_update_settings():
    config = get_config()
    return config.get("docker_auto_update_settings", {"enabled": True, "type": "cron", "value": "03:00"})

@router.post("/auto-update/settings")
async def save_auto_update_settings(settings: DockerAutoUpdateSettings):
    config = get_config()
    config["docker_auto_update_settings"] = settings.dict()
    save_config(config)
    
    # 异步触发调度器重载
    asyncio.create_task(DockerService.reload_scheduler())
    
    return {"message": "Settings updated and scheduler reloaded"}