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

    def list_containers(self, all=True, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        # 优先尝试通过 docker-py 客户端获取（效率高，数据全）
        if self.client:
            try:
                # 传入 filters 参数
                containers = self.client.containers.list(all=all, filters=filters)
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

    async def get_image_update_info(self, image_tag: str):
        """
        获取镜像的更新信息。支持 Docker Hub 以及第三方仓库 (如 lscr.io, ghcr.io)。
        """
        if not image_tag: return None
        
        # 1. 解析镜像名与仓库地址
        # lscr.io/linuxserver/qbittorrent:latest -> host=lscr.io, repo=linuxserver/qbittorrent, tag=latest
        # nginx -> host=registry-1.docker.io, repo=library/nginx, tag=latest
        parts = image_tag.split("/")
        host = "registry-1.docker.io"
        repo = ""
        tag = "latest"
        
        full_repo_path = image_tag
        if ":" in image_tag:
            full_repo_path, tag = image_tag.rsplit(":", 1)
            
        if "." in parts[0] or ":" in parts[0]:
            host = parts[0]
            repo = "/".join(parts[1:])
            if ":" in repo: repo = repo.rsplit(":", 1)[0]
        else:
            repo = full_repo_path
            if "/" not in repo:
                repo = f"library/{repo}"
        
        # 修正 Docker Hub 的主机名
        reg_host = host
        if host == "docker.io": reg_host = "registry-1.docker.io"
            
        # 2. 获取本地 RepoDigests
        local_digests = []
        res = self.exec_command(f"docker inspect --format='{{{{json .RepoDigests}}}}' {image_tag}", log_error=False)
        if res["success"] and res["stdout"].strip():
            try:
                import json
                local_digests = json.loads(res["stdout"])
            except: pass
            
        if not local_digests and self.client:
            try:
                img = self.client.images.get(image_tag)
                local_digests = img.attrs.get("RepoDigests", [])
            except: pass
            
        # 3. 动态获取远程 Digest (支持 OCI 挑战认证)
        remote_digest = ""
        try:
            from app.utils.http_client import get_async_client
            # 扩展 Accept 头，支持多架构镜像清单
            accept_headers = (
                "application/vnd.docker.distribution.manifest.v2+json, "
                "application/vnd.docker.distribution.manifest.list.v2+json, "
                "application/vnd.oci.image.manifest.v1+json, "
                "application/vnd.oci.image.index.v1+json"
            )
            
            async with get_async_client(timeout=15.0) as client:
                manifest_url = f"https://{reg_host}/v2/{repo}/manifests/{tag}"
                headers = {"Accept": accept_headers}
                
                # 显式开启重定向跟随
                res = await client.get(manifest_url, headers=headers, follow_redirects=True)
                
                if res.status_code == 401:
                    auth_header = res.headers.get("WWW-Authenticate", "")
                    if "Bearer" in auth_header:
                        import re
                        realm = re.search(r'realm="([^"]+)"', auth_header).group(1)
                        service_match = re.search(r'service="([^"]+)"', auth_header)
                        service = service_match.group(1) if service_match else ""
                        scope_match = re.search(r'scope="([^"]+)"', auth_header)
                        scope = scope_match.group(1) if scope_match else f"repository:{repo}:pull"
                        
                        auth_params = {"scope": scope}
                        if service: auth_params["service"] = service
                        
                        auth_res = await client.get(realm, params=auth_params, follow_redirects=True)
                        if auth_res.status_code == 200:
                            token = auth_res.json().get("token") or auth_res.json().get("access_token")
                            headers["Authorization"] = f"Bearer {token}"
                            res = await client.get(manifest_url, headers=headers, follow_redirects=True)
                
                if res.status_code == 200:
                    remote_digest = res.headers.get("Docker-Content-Digest", "")
                else:
                    logger.debug(f"HTTP {res.status_code} for {manifest_url}")
        except Exception as e:
            logger.warning(f"Failed to fetch remote digest for {image_tag} on {host}: {e}")

        # 4. 对比判定
        has_update = False
        if remote_digest:
            is_latest = any(remote_digest in d for d in local_digests)
            has_update = not is_latest
            status_text = "发现新版本" if has_update else "已是最新"
            logger.info(f"🔍 [镜像检测] 站点: {host} | 镜像: {repo}:{tag}")
            logger.info(f"   ┣ 本地指纹: {local_digests}")
            logger.info(f"   ┣ 远程指纹: {remote_digest}")
            logger.info(f"   ┗ 判定结果: {status_text}")
        else:
            logger.warning(f"⚠️ [镜像检测] 无法获取远程指纹: {image_tag} (Host: {host})")

        return {
            "image": image_tag,
            "local_digests": local_digests,
            "remote_digest": remote_digest,
            "has_update": has_update
        }

    @staticmethod
    async def run_auto_update_task():
        """
        极致精准版：根据记录中的 host_id 直接定点更新
        """
        logger.info("🚀 [Docker] 开始执行每日自动更新任务...")
        from app.core.config_manager import get_config
        from app.services.notification_service import NotificationService
        
        config = get_config()
        # 检查是否全局开启了自动更新
        auto_settings = config.get("docker_auto_update_settings", {"enabled": True})
        if not auto_settings.get("enabled"):
            logger.info("ℹ️ [Docker] 自动更新已全局关闭，跳过执行。")
            return

        all_hosts = config.get("docker_hosts", [])
        container_settings = config.get("docker_container_settings", {})
        
        # 1. 筛选出所有开启了自动更新且有 host_id 的记录
        tasks_by_host = {}
        for name, settings in container_settings.items():
            if settings.get("auto_update") and settings.get("host_id"):
                h_id = settings.get("host_id")
                if h_id not in tasks_by_host:
                    tasks_by_host[h_id] = []
                tasks_by_host[h_id].append(name)
        
        if not tasks_by_host:
            logger.info("ℹ️ [Docker] 没有发现待更新的任务记录，任务结束。")
            return

        updated_count = 0
        error_count = 0

        # 2. 定点执行
        for h_id, names in tasks_by_host.items():
            host_config = next((h for h in all_hosts if h.get("id") == h_id), None)
            if not host_config:
                logger.error(f"❌ [Docker] 找不到 ID 为 {h_id} 的主机配置，跳过容器: {names}")
                continue

            host_name = host_config.get("name", "Unknown")
            logger.info(f"🌐 [Docker] 正在连接主机 [{host_name}] 检查容器: {', '.join(names)}")
            
            try:
                from app.services.docker_service import DockerService
                service = DockerService(host_config)
                containers = service.list_containers(all=True, filters={"name": names})
                
                for container in containers:
                    c_name = container.get("name")
                    if c_name in names:
                        image = container.get("image")
                        try:
                            update_info = await service.get_image_update_info(image)
                            if update_info and update_info.get("has_update"):
                                logger.info(f"✨ [Docker][{host_name}] 发现镜像更新: {c_name}")
                                c_id = container.get("full_id") or container.get("id")
                                if service.container_action(c_id, "recreate"):
                                    updated_count += 1
                                    await NotificationService.emit(
                                        event="docker.auto_update",
                                        title="Docker 自动更新成功",
                                        message=f"主机: {host_name}\n容器: {c_name}\n镜像: {image}\n结果: 已更新并重构"
                                    )
                                else:
                                    error_count += 1
                        except Exception as e:
                            logger.error(f"❌ [Docker][{host_name}] 处理 {c_name} 异常: {e}")
                            error_count += 1
            except Exception as e:
                logger.error(f"❌ [Docker] 无法连接主机 {host_name}: {e}")
                error_count += len(names)

        logger.info(f"🏁 [Docker] 自动更新完毕。更新: {updated_count}, 失败: {error_count}")

    _scheduler = None
    _is_running = False

    @classmethod
    def get_scheduler(cls):
        if cls._scheduler is None:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            import os
            import pytz
            tz_name = os.getenv("TZ", "UTC")
            try:
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.UTC
            cls._scheduler = AsyncIOScheduler(timezone=tz)
        return cls._scheduler

    @classmethod
    async def start_scheduler(cls):
        if not cls._is_running:
            cls.get_scheduler().start()
            cls._is_running = True
            logger.info("📅 [Docker] 自动更新调度器已启动")
            await cls.reload_scheduler()

    @classmethod
    async def reload_scheduler(cls):
        """重载调度器设置"""
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger
        from app.core.config_manager import get_config
        import os
        import pytz
        
        scheduler = cls.get_scheduler()
        scheduler.remove_all_jobs()
        
        config = get_config()
        settings = config.get("docker_auto_update_settings", {"enabled": True, "type": "cron", "value": "03:00"})
        
        if not settings.get("enabled"):
            logger.info("📅 [Docker] 自动更新已停用")
            return

        tz_name = os.getenv("TZ", "UTC")
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.UTC

        try:
            stype = settings.get("type", "cron")
            sval = settings.get("value", "03:00")
            
            if stype == "cron":
                if ":" in sval:
                    h, m = sval.split(":")
                    trigger = CronTrigger(hour=int(h), minute=int(m), timezone=tz)
                else:
                    trigger = CronTrigger.from_crontab(sval, timezone=tz)
            else: # interval (minutes)
                trigger = IntervalTrigger(minutes=int(sval), timezone=tz)

            scheduler.add_job(
                DockerService.run_auto_update_task,
                trigger,
                id="docker_auto_update",
                replace_existing=True
            )
            logger.info(f"📅 [Docker] 自动更新已重载 ({stype}: {sval}, 时区: {tz_name})")
        except Exception as e:
            logger.error(f"❌ [Docker] 重载调度器失败: {e}")
        # ... (rest of the method logic)

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