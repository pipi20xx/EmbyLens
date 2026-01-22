import docker
import paramiko
import os
import time
from typing import List, Dict, Any, Optional
from app.utils.logger import logger
from app.core.config_manager import get_config

# --- 深度补丁：彻底解决 known_hosts 和 密码支持问题 ---

# 1. 强制策略补丁：禁止拒绝新主机
_original_set_policy = paramiko.SSHClient.set_missing_host_key_policy
def _forced_set_policy(self, policy):
    return _original_set_policy(self, paramiko.AutoAddPolicy())
paramiko.SSHClient.set_missing_host_key_policy = _forced_set_policy

# 2. 密码注入补丁
_original_connect = paramiko.SSHClient.connect
def _patched_connect(self, hostname, port=22, username=None, password=None, **kwargs):
    if not password:
        config = get_config()
        hosts = config.get("docker_hosts", [])
        host_match = next((h for h in hosts if h.get("ssh_host") == hostname), None)
        if host_match and host_match.get("ssh_pass"):
            password = host_match.get("ssh_pass")
    
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
                base_url = f"ssh://{ssh_user}@{ssh_host}:{ssh_port}"
                return docker.DockerClient(base_url=base_url, use_ssh_client=False, timeout=15)
            
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
        # 优先尝试通过 docker-py 客户端获取（效率高，数据全）
        if self.client:
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
                logger.warning(f"Docker-py client failed, falling back to SSH Shell: {e}")

        # 如果客户端不可用或报错，通过 SSH 执行 docker ps 命令解析 (纯 SSH 模式)
        if self.host_config.get("type") == "ssh":
            cmd = "docker ps -a --format '{{json .}}'" if all else "docker ps --format '{{json .}}'"
            res = self.exec_command(cmd)
            if res["success"]:
                try:
                    import json
                    lines = res["stdout"].strip().split('\n')
                    results = []
                    for line in lines:
                        if not line: continue
                        c = json.loads(line)
                        results.append({
                            "id": c.get("ID"),
                            "full_id": c.get("ID"),
                            "name": c.get("Names"),
                            "image": c.get("Image"),
                            "status": c.get("Status").lower().split(' ')[0], # "Up 2 hours" -> "up"
                            "created": c.get("CreatedAt"),
                            "ports": c.get("Ports")
                        })
                    return results
                except Exception as e:
                    logger.error(f"Failed to parse docker ps output: {e}")
        return []

    def container_action(self, container_id: str, action: str):
        if not self.client: return False
        try:
            container = self.client.containers.get(container_id)
            if action == "start": container.start()
            elif action == "stop": container.stop()
            elif action == "restart": container.restart()
            elif action == "remove": container.remove(force=True)
            elif action in ["recreate", "update"]:
                attrs = container.attrs
                image_tag = attrs['Config']['Image']
                name = attrs['Name'].lstrip('/')
                
                # 无论 recreate 还是 update，都执行 pull（保持与网页版逻辑一致）
                logger.info(f"📥 [Docker] 正在为容器 {name} 拉取最新镜像: {image_tag}")
                try:
                    self.client.images.pull(image_tag)
                except Exception as e:
                    logger.warning(f"⚠️ [Docker] 拉取镜像失败，将尝试使用本地镜像: {e}")

                # 提取完整配置
                config = attrs.get('Config', {})
                host_config = attrs.get('HostConfig', {})
                
                # 转换端口映射格式 (docker-py run 需要格式: { 'container_port/proto': 'host_port' })
                port_bindings = host_config.get('PortBindings') or {}
                ports = {}
                if port_bindings:
                    for container_port, host_ports in port_bindings.items():
                        if host_ports:
                            ports[container_port] = host_ports[0].get('HostPort')
                
                network_mode = host_config.get('NetworkMode', 'bridge')
                
                # 修复：如果网络模式是 host，则不能传递 ports 参数，否则报错
                if network_mode == "host":
                    ports = None

                create_kwargs = {
                    "image": image_tag,
                    "name": name,
                    "detach": True,
                    "environment": config.get('Env', []),
                    "volumes": host_config.get('Binds', []),
                    "ports": ports,
                    "restart_policy": host_config.get('RestartPolicy', {}),
                    "network_mode": network_mode,
                    "command": config.get('Cmd'),
                    "entrypoint": config.get('Entrypoint'),
                    "working_dir": config.get('WorkingDir'),
                    "user": config.get('User'),
                    "hostname": config.get('Hostname'),
                    "mac_address": config.get('MacAddress'),
                    "labels": config.get('Labels')
                }
                
                # 特殊处理：如果原容器有特权，新容器也要有
                if host_config.get('Privileged'):
                    create_kwargs["privileged"] = True

                # 安全重构策略：先重命名旧容器，失败则回滚
                old_name = container.name
                bak_name = f"{old_name}_lens_bak_{int(time.time())}"
                
                try:
                    container.stop()
                    container.rename(bak_name)
                    
                    # 创建并启动新容器
                    self.client.containers.run(**create_kwargs)
                    
                    # 新容器启动成功，删除备份
                    container.remove(force=True)
                    logger.info(f"✨ [Docker] 容器 {old_name} 重构成功，已清理旧容器")
                except Exception as run_err:
                    logger.error(f"❌ [Docker] 新容器启动失败，尝试回滚: {run_err}")
                    # 尝试恢复旧容器
                    try:
                        # 检查新容器是否已半途创建（如果创建了但没启动成功，也需要清理掉名称占位）
                        try:
                            failed_new = self.client.containers.get(old_name)
                            failed_new.remove(force=True)
                        except: pass
                        
                        container.rename(old_name)
                        container.start()
                        logger.info(f"⏪ [Docker] 已成功回滚至旧容器 {old_name}")
                    except Exception as rollback_err:
                        logger.error(f"🚨 [Docker] 回滚失败! 旧容器目前名称为 {bak_name}: {rollback_err}")
                    raise run_err
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

    def exec_command(self, command: str, cwd: Optional[str] = None, log_error: bool = True) -> Dict[str, Any]:
        """在远程或本地执行 shell 命令"""
        import subprocess
        full_cmd = f"cd {cwd} && {command}" if cwd else command
        
        # 噪音过滤器：过滤掉那些无害但烦人的 Docker 警告
        noise_filters = [
            "the attribute `version` is obsolete",
            "search/all: the attribute `version` is obsolete",
            "recreate: the attribute `version` is obsolete"
        ]

        def filter_noise(text: str) -> str:
            if not text: return ""
            lines = text.split('\n')
            # 只有当该行不包含任何噪音片段时才保留
            filtered = [line for line in lines if not any(noise in line for noise in noise_filters)]
            return '\n'.join(filtered).strip()

        if self.host_config.get("type") == "local":
            try:
                process = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
                stdout = process.stdout
                stderr = filter_noise(process.stderr)
                
                if process.returncode != 0 and log_error:
                    logger.error(f"Local Command Failed: {command} (Code: {process.returncode}, Err: {stderr})")
                return {"success": process.returncode == 0, "stdout": stdout, "stderr": stderr}
            except Exception as e:
                return {"success": False, "stdout": "", "stderr": str(e)}
        
        elif self.host_config.get("type") == "ssh":
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh_host = self.host_config.get("ssh_host")
                ssh_user = self.host_config.get("ssh_user", "root")
                ssh_port = self.host_config.get("ssh_port", 22)
                ssh_pass = self.host_config.get("ssh_pass")
                
                ssh.connect(ssh_host, port=ssh_port, username=ssh_user, password=ssh_pass, timeout=10)
                stdin, stdout, stderr = ssh.exec_command(full_cmd)
                
                out = stdout.read().decode()
                err = filter_noise(stderr.read().decode())
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0 and log_error:
                    logger.error(f"SSH Command Failed: {command} (Code: {exit_status}, Err: {err})")
                
                return {
                    "success": exit_status == 0,
                    "stdout": out,
                    "stderr": err
                }
            except Exception as e:
                if log_error: logger.error(f"SSH Connection Error during exec: {e}")
                return {"success": False, "stdout": "", "stderr": str(e)}
            finally:
                ssh.close()
        return {"success": False, "stdout": "", "stderr": "Unsupported host type"}

    def read_file(self, file_path: str) -> str:
        if self.host_config.get("type") == "local":
            if not os.path.exists(file_path): return ""
            with open(file_path, "r") as f: return f.read()
            
        elif self.host_config.get("type") == "ssh":
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(self.host_config.get("ssh_host"), 
                            port=self.host_config.get("ssh_port", 22), 
                            username=self.host_config.get("ssh_user"), 
                            password=self.host_config.get("ssh_pass"))
                sftp = ssh.open_sftp()
                with sftp.open(file_path, 'r') as f:
                    content = f.read().decode()
                sftp.close()
                return content
            except Exception as e:
                logger.error(f"SFTP Read Error: {e}")
                return ""
            finally:
                ssh.close()
        return ""

    def write_file(self, file_path: str, content: str) -> bool:
        if self.host_config.get("type") == "local":
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f: f.write(content)
                return True
            except: return False
            
        elif self.host_config.get("type") == "ssh":
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(self.host_config.get("ssh_host"), 
                            port=self.host_config.get("ssh_port", 22), 
                            username=self.host_config.get("ssh_user"), 
                            password=self.host_config.get("ssh_pass"))
                sftp = ssh.open_sftp()
                remote_dir = os.path.dirname(file_path)
                ssh.exec_command(f"mkdir -p {remote_dir}")
                with sftp.open(file_path, 'w') as f:
                    f.write(content)
                sftp.close()
                return True
            except Exception as e:
                logger.error(f"SFTP Write Error: {e}")
                return False
            finally:
                ssh.close()
        return False

    def get_container_socket(self, container_id: str, command: str = "/bin/bash"):
        """获取容器的交互式 Socket"""
        if not self.client:
            return None
        
        try:
            # 使用 APIClient 以获得对底层 socket 的访问权限
            api_client = self.client.api
            exec_instance = api_client.exec_create(
                container_id, 
                cmd=command, 
                stdin=True, 
                stdout=True, 
                stderr=True, 
                tty=True
            )
            
            # 返回 socket 供 WebSocket 使用
            sock = api_client.exec_start(exec_instance['Id'], detach=False, tty=True, stream=True, socket=True)
            return sock
        except Exception as e:
            logger.error(f"Failed to create exec socket: {e}")
            if command == "/bin/bash":
                # 尝试退回到 /bin/sh
                return self.get_container_socket(container_id, "/bin/sh")
            return None