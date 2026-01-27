import os
import re
import uuid
import asyncio
import subprocess
import hashlib
import tempfile
import docker
import paramiko
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlparse, urlunparse

from . import models, schemas
from app.utils.logger import logger
from app.core.config_manager import get_config
from app.services.docker_service import DockerService

BUILD_LOG_DIR = Path("/app/data/logs/builds")
BUILD_LOG_DIR.mkdir(parents=True, exist_ok=True)

TASK_LOG_SENTINEL = "--- TASK_COMPLETED ---"

class ImageBuilderService:
    @staticmethod
    async def get_projects(db: AsyncSession) -> List[models.BuildProject]:
        result = await db.execute(select(models.BuildProject).order_by(models.BuildProject.name))
        return result.scalars().all()

    @staticmethod
    async def create_project(db: AsyncSession, project: schemas.ProjectCreate) -> models.BuildProject:
        db_project = models.BuildProject(id=str(uuid.uuid4()), **project.dict())
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        return db_project

    @staticmethod
    async def get_project(db: AsyncSession, project_id: str) -> Optional[models.BuildProject]:
        result = await db.execute(select(models.BuildProject).where(models.BuildProject.id == project_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_project(db: AsyncSession, project_id: str, project_in: schemas.ProjectUpdate) -> Optional[models.BuildProject]:
        db_project = await ImageBuilderService.get_project(db, project_id)
        if not db_project:
            return None
        
        update_data = project_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)
        
        await db.commit()
        await db.refresh(db_project)
        return db_project

    @staticmethod
    async def delete_project(db: AsyncSession, project_id: str) -> bool:
        db_project = await ImageBuilderService.get_project(db, project_id)
        if not db_project:
            return False
        await db.delete(db_project)
        await db.commit()
        return True

    # --- Registry CRUD ---
    @staticmethod
    async def get_registries(db: AsyncSession) -> List[models.BuildRegistry]:
        result = await db.execute(select(models.BuildRegistry).order_by(models.BuildRegistry.name))
        return result.scalars().all()

    @staticmethod
    async def create_registry(db: AsyncSession, registry: schemas.RegistryCreate) -> models.BuildRegistry:
        db_registry = models.BuildRegistry(id=str(uuid.uuid4()), **registry.dict())
        db.add(db_registry)
        await db.commit()
        await db.refresh(db_registry)
        return db_registry

    @staticmethod
    async def get_registry(db: AsyncSession, registry_id: str) -> Optional[models.BuildRegistry]:
        result = await db.execute(select(models.BuildRegistry).where(models.BuildRegistry.id == registry_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_registry(db: AsyncSession, registry_id: str, registry_in: schemas.RegistryUpdate) -> Optional[models.BuildRegistry]:
        db_registry = await ImageBuilderService.get_registry(db, registry_id)
        if not db_registry: return None
        update_data = registry_in.dict(exclude_unset=True)
        for key, value in update_data.items(): setattr(db_registry, key, value)
        await db.commit()
        await db.refresh(db_registry)
        return db_registry

    @staticmethod
    async def delete_registry(db: AsyncSession, registry_id: str) -> bool:
        db_registry = await ImageBuilderService.get_registry(db, registry_id)
        if not db_registry:
            return False
        await db.delete(db_registry)
        await db.commit()
        return True

    @staticmethod
    async def test_registry(db: AsyncSession, registry_id: str):
        registry = await ImageBuilderService.get_registry(db, registry_id)
        if not registry:
            return {"success": False, "message": "仓库配置不存在"}
        
        credential = None
        if registry.credential_id:
            credential = await ImageBuilderService.get_credential(db, registry.credential_id)
        
        # 1. 构造强制协议的 URL
        raw_url = registry.url.replace("https://", "").replace("http://", "")
        protocol = "https" if registry.is_https else "http"
        api_url = f"{protocol}://{raw_url.rstrip('/')}/v2/"

        # 2. 强一致性协议检测
        try:
            # 尝试连接用户选择的协议
            requests.get(api_url, timeout=5, verify=False)
        except Exception:
            # 如果用户选了 HTTPS 但失败了，探测一下是不是其实只支持 HTTP
            if registry.is_https:
                try:
                    http_test_url = f"http://{raw_url.rstrip('/')}/v2/"
                    h_resp = requests.get(http_test_url, timeout=3)
                    if h_resp.status_code in [200, 401]:
                        return {"success": False, "message": f"❌ 协议不匹配: 该仓库似乎只支持 HTTP，请切换设置"}
                except:
                    pass
            return {"success": False, "message": f"连接失败: 无法通过 {protocol.upper()} 访问该地址"}

        # 3. 登录验证逻辑
        if credential:
            config = get_config()
            hosts = config.get("docker_hosts", [])
            host_config = hosts[0] if hosts else {"type": "local", "name": "Local Host"}
            service = DockerService(host_config)
            
            login_cmd = f"echo \"{credential.encrypted_password}\" | docker login -u \"{credential.username}\" --password-stdin {raw_url}"
            res = service.exec_command(login_cmd, log_error=False)
            
            if res["success"]:
                return {"success": True, "message": f"✅ 登录成功: 协议和凭据均已验证"}
            else:
                err = res["stderr"] or res["stdout"]
                return {"success": False, "message": f"鉴权失败: {err[:200]}"}
        else:
            return {"success": True, "message": f"✅ 连接成功 ({protocol.upper()}): 该地址有效"}

    # --- Credential CRUD ---
    @staticmethod
    async def get_credentials(db: AsyncSession) -> List[models.BuildCredential]:
        result = await db.execute(select(models.BuildCredential).order_by(models.BuildCredential.name))
        return result.scalars().all()

    @staticmethod
    async def create_credential(db: AsyncSession, cred: schemas.CredentialCreate) -> models.BuildCredential:
        db_cred = models.BuildCredential(
            id=str(uuid.uuid4()), 
            name=cred.name, 
            username=cred.username, 
            encrypted_password=cred.password
        )
        db.add(db_cred)
        await db.commit()
        await db.refresh(db_cred)
        return db_cred

    @staticmethod
    async def get_credential(db: AsyncSession, cred_id: str) -> Optional[models.BuildCredential]:
        result = await db.execute(select(models.BuildCredential).where(models.BuildCredential.id == cred_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_credential(db: AsyncSession, cred_id: str, cred_in: schemas.CredentialUpdate) -> Optional[models.BuildCredential]:
        db_cred = await ImageBuilderService.get_credential(db, cred_id)
        if not db_cred: return None
        update_data = cred_in.dict(exclude_unset=True)
        if 'password' in update_data:
            if update_data['password']: # 有输入新密码
                db_cred.encrypted_password = update_data['password']
            del update_data['password']
        for key, value in update_data.items(): setattr(db_cred, key, value)
        await db.commit()
        await db.refresh(db_cred)
        return db_cred

    @staticmethod
    async def delete_credential(db: AsyncSession, cred_id: str) -> bool:
        db_cred = await ImageBuilderService.get_credential(db, cred_id)
        if not db_cred:
            return False
        await db.delete(db_cred)
        await db.commit()
        return True

    # --- Proxy CRUD ---
    @staticmethod
    async def get_proxies(db: AsyncSession) -> List[models.BuildProxy]:
        result = await db.execute(select(models.BuildProxy).order_by(models.BuildProxy.name))
        return result.scalars().all()

    @staticmethod
    async def create_proxy(db: AsyncSession, proxy: schemas.ProxyCreate) -> models.BuildProxy:
        db_proxy = models.BuildProxy(id=str(uuid.uuid4()), **proxy.dict())
        db.add(db_proxy)
        await db.commit()
        await db.refresh(db_proxy)
        return db_proxy

    @staticmethod
    async def get_proxy(db: AsyncSession, proxy_id: str) -> Optional[models.BuildProxy]:
        result = await db.execute(select(models.BuildProxy).where(models.BuildProxy.id == proxy_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_proxy(db: AsyncSession, proxy_id: str, proxy_in: schemas.ProxyUpdate) -> Optional[models.BuildProxy]:
        db_proxy = await ImageBuilderService.get_proxy(db, proxy_id)
        if not db_proxy: return None
        update_data = proxy_in.dict(exclude_unset=True)
        for key, value in update_data.items(): setattr(db_proxy, key, value)
        await db.commit()
        await db.refresh(db_proxy)
        return db_proxy

    @staticmethod
    async def delete_proxy(db: AsyncSession, proxy_id: str) -> bool:
        db_proxy = await ImageBuilderService.get_proxy(db, proxy_id)
        if not db_proxy:
            return False
        await db.delete(db_proxy)
        await db.commit()
        return True

    # --- System Info ---
    @staticmethod
    async def get_system_info(host_id: str):
        config = get_config()
        hosts = config.get("docker_hosts", [])
        host_config = next((h for h in hosts if h.get("id") == host_id), None)
        
        if not host_config:
            return {"error": "Host not found"}

        service = DockerService(host_config)
        info = {
            "docker_version": "Unknown",
            "buildx_version": "Not Found",
            "builders": [],
            "platforms": []
        }
        
        try:
            # Version
            res = service.exec_command("docker version --format '{{.Server.Version}}'")
            if res["success"]:
                info["docker_version"] = res["stdout"].strip()
            
            # Buildx
            res = service.exec_command("docker buildx version")
            if res["success"]:
                info["buildx_version"] = res["stdout"].strip()
            
            # Platforms extraction (Robust version for older buildx)
            res = service.exec_command("docker buildx inspect")
            if res["success"] and res["stdout"]:
                match = re.search(r"Platforms:\s*(.+)", res["stdout"])
                if match:
                    plat_str = match.group(1).strip()
                    info["platforms"] = sorted(list(set(p.strip() for p in plat_str.split(",") if p.strip())))

            # Builders
            res = service.exec_command("docker buildx ls")
            if res["success"]:
                info["builders"] = res["stdout"].splitlines()
        except Exception as e:
            logger.error(f"Error getting remote system info: {e}")
            
        return info

    @staticmethod
    async def setup_buildx_env(host_id: str, proxy_id: Optional[str] = None):
        config = get_config()
        hosts = config.get("docker_hosts", [])
        host_config = next((h for h in hosts if h.get("id") == host_id), None)
        if not host_config:
            return {"success": False, "message": "Host not found"}

        service = DockerService(host_config)
        logs = []
        
        # 获取代理配置
        proxy_env = ""
        if proxy_id:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                proxy = await ImageBuilderService.get_proxy(db, proxy_id)
                if proxy:
                    url = proxy.url
                    if proxy.username and proxy.password:
                        parsed = urlparse(url)
                        netloc = f"{proxy.username}:{proxy.password}@{parsed.netloc}"
                        url = urlunparse(parsed._replace(netloc=netloc))
                    # 构造 buildx create 的环境变量参数
                    proxy_env = f"--driver-opt env.http_proxy={url} --driver-opt env.https_proxy={url} --driver-opt env.no_proxy=localhost,127.0.0.1"
                    logs.append(f"--- 绑定构建代理: {proxy.url} ---")

        # 1. Install QEMU binfmt handlers
        logs.append("正在安装 QEMU 多架构仿真支持...")
        res = service.exec_command("docker run --privileged --rm tonistiigi/binfmt --install all")
        logs.append(res["stdout"] + res["stderr"])
        
        # 2. Create specialized builder
        logs.append("正在清理并重建专用构建器 (lens-builder)...")
        # 强制删除旧的，以便应用新的代理设置
        service.exec_command("docker buildx rm lens-builder")
        
        create_cmd = f"docker buildx create --name lens-builder --driver docker-container --driver-opt network=host {proxy_env} --use"
        res = service.exec_command(create_cmd)
        logs.append(res["stdout"] + res["stderr"])
            
        # 3. Bootstrap
        service.exec_command("docker buildx inspect --bootstrap")
        
        return {"success": True, "logs": "\n".join(logs)}

    # --- Task Logic ---
    @staticmethod
    async def get_task_logs(db: AsyncSession, project_id: str) -> List[models.BuildTaskLog]:
        result = await db.execute(
            select(models.BuildTaskLog)
            .where(models.BuildTaskLog.project_id == project_id)
            .order_by(models.BuildTaskLog.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def create_task_log(db: AsyncSession, project_id: str, tag: str) -> str:
        task_id = str(uuid.uuid4())
        db_task = models.BuildTaskLog(id=task_id, project_id=project_id, tag=tag)
        db.add(db_task)
        await db.commit()
        return task_id

    @staticmethod
    async def update_task_status(db: AsyncSession, task_id: str, status: str):
        await db.execute(
            update(models.BuildTaskLog)
            .where(models.BuildTaskLog.id == task_id)
            .values(status=status)
        )
        await db.commit()

    @staticmethod
    def run_docker_task_sync(task_id: str, project_dict: dict, tag_input: str, cred_dict: Optional[dict], proxy_dict: Optional[dict], host_config: dict):
        log_file_path = BUILD_LOG_DIR / f"{task_id}.log"
        
        def log_to_file(message: str):
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(message.strip() + "\n")

        service = DockerService(host_config)
        tags = [t.strip() for t in re.split(r'[,，|]', tag_input) if t.strip()]
        if not tags: tags = ["latest"]

        p = project_dict
        platforms = [plat.strip() for plat in p.get('platforms', 'linux/amd64').split(',') if plat.strip()]
        
        final_status = "FAILED"
        try:
            log_to_file(f"✅ 远程构建任务已启动... (主机: {host_config.get('name')})")
            
            # 1. Login
            if cred_dict:
                log_to_file(f"--- 正在远程登录仓库: {cred_dict.get('registry_url')} ---")
                login_cmd = f"echo \"{cred_dict['encrypted_password']}\" | docker login -u \"{cred_dict['username']}\" --password-stdin {cred_dict.get('registry_url', '')}"
                res = service.exec_command(login_cmd)
                if not res["success"]:
                    log_to_file(f"❌ 登录失败: {res['stderr']}")
                else:
                    log_to_file("--- 登录成功 ---")

            # 2. Proxy & Build
            build_args = []
            if proxy_dict:
                url = proxy_dict['url']
                if proxy_dict.get('username') and proxy_dict.get('password'):
                    parsed = urlparse(url)
                    netloc = f"{proxy_dict['username']}:{proxy_dict['password']}@{parsed.netloc}"
                    url = urlunparse(parsed._replace(netloc=netloc))
                
                log_to_file(f"--- 🚀 注入代理: {proxy_dict['url']} ---")
                for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                    build_args.append(f"--build-arg {key}={url}")

            # Prepare tags
            reg_url = p.get('registry_url', 'docker.io')
            if "://" in reg_url:
                reg_host = urlparse(reg_url).netloc
            else:
                reg_host = urlparse(f"https://{reg_url}").netloc
                if not reg_host: reg_host = reg_url.split('/')[0]

            is_dockerhub = reg_host in ["docker.io", "index.docker.io", "registry-1.docker.io", ""]
            
            if is_dockerhub:
                repo_base = p['repo_image_name']
                log_to_file(f"--- 目标仓库判定为: Docker Hub ---")
            else:
                repo_base = f"{reg_host}/{p['repo_image_name']}".replace("//", "/")
                log_to_file(f"--- 目标仓库判定为私有仓库: {reg_host} ---")
            
            tag_args = " ".join([f"-t {repo_base}:{t}" for t in tags])

            # Cache Strategy
            cache_args = []
            if not p.get('no_cache'):
                primary_tag = tags[0]
                cache_args.append(f"--cache-from=type=registry,ref={repo_base}:{primary_tag}")
                cache_args.append("--cache-to=type=inline")
                log_to_file(f"--- ♻️ 缓存策略: 尝试复用远程缓存 (初次构建报错 NotFound 属正常现象) ---")
            else:
                cache_args.append("--no-cache")
                log_to_file("--- ⚡ 缓存策略: 强制无缓存构建 ---")

            # Unify build logic
            log_to_file(f"\n--- 正在准备构建环境 ---")
            
            # 自动探测构建器
            builder_to_use = "default"
            check_builder = service.exec_command("docker buildx inspect lens-builder", log_error=False)
            if check_builder["success"]:
                builder_to_use = "lens-builder"
                log_to_file(f"--- 🚀 构建模式: 专用容器构建 (Builder: lens-builder, Driver: docker-container) ---")
            else:
                log_to_file(f"--- 💻 构建模式: 宿主机原生构建 (Builder: default, Driver: docker) ---")

            log_to_file(f"--- 开始远程构建与推送 (平台: {','.join(platforms)}, Tags: {' / '.join(tags)}) ---")
            build_cmd = f"docker buildx build --builder {builder_to_use} --platform {','.join(platforms)} -f {p['dockerfile_path']} {tag_args} {' '.join(build_args)} {' '.join(cache_args)} --push ."
            log_to_file(f"执行命令: {build_cmd}")
            
            if host_config.get("type") == "ssh":
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host_config['ssh_host'], port=host_config.get('ssh_port', 22), 
                            username=host_config.get('ssh_user'), password=host_config.get('ssh_pass'))
                
                full_cmd = f"cd {p['build_context']} && {build_cmd}"
                stdin, stdout, stderr = ssh.exec_command(full_cmd)
                
                while not stdout.channel.exit_status_ready():
                    if stdout.channel.recv_ready():
                        log_to_file(stdout.channel.recv(1024).decode('utf-8', 'ignore'))
                    if stderr.channel.recv_stderr_ready():
                        log_to_file(stderr.channel.recv_stderr(1024).decode('utf-8', 'ignore'))
                    import time
                    time.sleep(0.1)
                
                while stdout.channel.recv_ready():
                    log_to_file(stdout.channel.recv(1024).decode('utf-8', 'ignore'))
                while stderr.channel.recv_stderr_ready():
                    log_to_file(stderr.channel.recv_stderr(1024).decode('utf-8', 'ignore'))
                
                exit_status = stdout.channel.recv_exit_status()
                log_to_file(f"--- 进程退出，退出码: {exit_status} ---")
                if exit_status == 0: final_status = "SUCCESS"
                ssh.close()
            else:
                res = service.exec_command(build_cmd, cwd=p['build_context'])
                log_to_file(res["stdout"])
                log_to_file(res["stderr"])
                log_to_file(f"--- 本地进程执行完毕，结果: {'成功' if res['success'] else '失败'} ---")
                if res["success"]: final_status = "SUCCESS"

            if final_status == "SUCCESS":
                log_to_file("\n--- ✅ 构建任务成功完成! ---")
            else:
                log_to_file("\n--- ❌ 构建任务失败 ---")

        except Exception as e:
            log_to_file(f"\n--- ❌ 发生严重错误 ---\n{e}")
        finally:
            log_to_file(TASK_LOG_SENTINEL)
            
        return final_status

    @staticmethod
    async def start_build_task(db: AsyncSession, project_id: str, tag: str):
        project = await ImageBuilderService.get_project(db, project_id)
        if not project: return
        
        config = get_config()
        hosts = config.get("docker_hosts", [])
        host_config = next((h for h in hosts if h.get("id") == project.host_id), None)
        if not host_config: host_config = {"type": "local", "name": "Local Host"}

        registry = await ImageBuilderService.get_registry(db, project.registry_id) if project.registry_id else None
        credential = await ImageBuilderService.get_credential(db, registry.credential_id) if registry and registry.credential_id else None
        proxy = await ImageBuilderService.get_proxy(db, project.proxy_id) if project.proxy_id else None
        
        task_id = await ImageBuilderService.create_task_log(db, project_id, tag)
        
        project_dict = {
            "name": project.name, "build_context": project.build_context,
            "dockerfile_path": project.dockerfile_path, "local_image_name": project.local_image_name,
            "repo_image_name": project.repo_image_name, "no_cache": project.no_cache,
            "auto_cleanup": project.auto_cleanup, "platforms": project.platforms,
            "registry_url": registry.url if registry else "docker.io",
            "is_https": registry.is_https if registry else True
        }
        
        cred_dict = {"username": credential.username, "encrypted_password": credential.encrypted_password, "registry_url": registry.url} if credential else None
        proxy_dict = {"url": proxy.url, "username": proxy.username, "password": proxy.password} if proxy else None

        def task_wrapper():
            from app.db.session import AsyncSessionLocal
            import asyncio
            status = ImageBuilderService.run_docker_task_sync(task_id, project_dict, tag, cred_dict, proxy_dict, host_config)
            async def update_db():
                async with AsyncSessionLocal() as new_db:
                    await ImageBuilderService.update_task_status(new_db, task_id, status)
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(update_db())
            except: pass

        asyncio.create_task(asyncio.to_thread(task_wrapper))
        return task_id
