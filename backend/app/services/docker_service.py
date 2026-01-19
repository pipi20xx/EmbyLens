import docker
import paramiko
from typing import List, Dict, Any, Optional
from app.utils.logger import logger
from app.core.config_manager import get_config

# --- 深度补丁：彻底解决 known_hosts 和 密码支持问题 ---

# 1. 强制策略补丁：禁止拒绝新主机
_original_set_policy = paramiko.SSHClient.set_missing_host_key_policy
def _forced_set_policy(self, policy):
    # 无论外界想设置什么策略（比如 docker-py 默认设置的 RejectPolicy），都强制改为 AutoAddPolicy
    return _original_set_policy(self, paramiko.AutoAddPolicy())
paramiko.SSHClient.set_missing_host_key_policy = _forced_set_policy

# 2. 密码注入补丁：拦截连接动作并注入密码
_original_connect = paramiko.SSHClient.connect
def _patched_connect(self, hostname, port=22, username=None, password=None, **kwargs):
    # 如果调用时没带密码，我们去配置里找找看
    if not password:
        config = get_config()
        hosts = config.get("docker_hosts", [])
        # 根据 IP 匹配对应的密码
        host_match = next((h for h in hosts if h.get("ssh_host") == hostname), None)
        if host_match and host_match.get("ssh_pass"):
            password = host_match.get("ssh_pass")
            # logger.info(f"Injecting password for SSH host: {hostname}")
    
    # 确保禁用了主机密钥检查 (双重保险)
    kwargs['allow_agent'] = False
    kwargs['look_for_keys'] = False
    return _original_connect(self, hostname, port=port, username=username, password=password, **kwargs)

paramiko.SSHClient.connect = _patched_connect

# --- Service 实现 ---

class DockerService:
    def __init__(self, host_config: Dict[str, Any]):
        self.host_config = host_config
        self.client = self._get_client()

    def _get_client(self):
        try:
            host_type = self.host_config.get("type", "local")
            if host_type == "local":
                return docker.from_env()
            
            elif host_type == "ssh":
                ssh_host = self.host_config.get("ssh_host")
                ssh_user = self.host_config.get("ssh_user", "root")
                ssh_port = self.host_config.get("ssh_port", 22)
                
                # 构建基础 URL
                base_url = f"ssh://{ssh_user}@{ssh_host}:{ssh_port}"
                
                # 必须使用 use_ssh_client=False 才能让 paramiko 补丁生效
                return docker.DockerClient(
                    base_url=base_url,
                    use_ssh_client=False,
                    timeout=15
                )
            
            elif host_type == "tcp":
                host = self.host_config.get("ssh_host")
                port = self.host_config.get("ssh_port", 2375)
                use_tls = self.host_config.get("use_tls", False)
                protocol = "https" if use_tls else "http"
                base_url = f"{protocol}://{host}:{port}"
                return docker.DockerClient(base_url=base_url)
                
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Docker host {self.host_config.get('name')}: {e}")
            return None

    def list_containers(self, all=True) -> List[Dict[str, Any]]:
        if not self.client: return []
        try:
            containers = self.client.containers.list(all=all)
            return [{
                "id": c.short_id,
                "full_id": c.id,
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.id,
                "status": c.status,
                "created": c.attrs.get("Created"),
                "ports": c.attrs.get("NetworkSettings", {}).get("Ports", {})
            } for c in containers]
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []

    def container_action(self, container_id: str, action: str):
        if not self.client: return False
        try:
            container = self.client.containers.get(container_id)
            if action == "start": container.start()
            elif action == "stop": container.stop()
            elif action == "restart": container.restart()
            elif action == "remove": container.remove(force=True)
            elif action == "recreate":
                # 获取原配置
                attrs = container.attrs
                image_tag = attrs['Config']['Image']
                name = attrs['Name'].lstrip('/')
                
                # 尝试拉取最新镜像 (Force Pull)
                logger.info(f"⚓ [Docker] 正在强制拉取最新镜像: {image_tag}")
                self.client.images.pull(image_tag)
                logger.info(f"🚚 [Docker] 镜像拉取完成，准备销毁旧容器: {name}")
                
                # 停止并移除旧容器
                container.stop()
                container.remove()
                logger.info(f"🔥 [Docker] 旧容器 {name} 已移除，正在使用原配置创建新容器...")
                
                # 重新创建
                create_kwargs = {
                    "image": image_tag,
                    "name": name,
                    "detach": True,
                    "environment": attrs['Config'].get('Env', []),
                    "volumes": attrs.get('HostConfig', {}).get('Binds', []),
                    "ports": {k: v[0]['HostPort'] if v else None for k, v in attrs.get('HostConfig', {}).get('PortBindings', {}).items()},
                    "restart_policy": attrs.get('HostConfig', {}).get('RestartPolicy', {}),
                    "network_mode": attrs.get('HostConfig', {}).get('NetworkMode', 'bridge')
                }
                self.client.containers.run(**create_kwargs)
                logger.info(f"✨ [Docker] 容器 {name} 重构完成并已启动")
            return True
        except Exception as e:
            logger.error(f"Error performing action {action} on container {container_id}: {e}")
            return False

    def get_container_logs(self, container_id: str, tail=100) -> str:
        if not self.client: return "Not connected to Docker"
        try:
            container = self.client.containers.get(container_id)
            return container.logs(tail=tail).decode("utf-8")
        except Exception as e:
            return str(e)

    def test_connection(self) -> bool:
        if not self.client: return False
        try:
            return self.client.ping()
        except Exception:
            return False