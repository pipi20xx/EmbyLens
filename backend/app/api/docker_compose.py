from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import shutil
import subprocess
from app.utils.logger import logger, audit_log
import time

router = APIRouter()

COMPOSE_DIR = "data/compose"

class ComposeProject(BaseModel):
    name: str
    content: str

def ensure_compose_dir():
    if not os.path.exists(COMPOSE_DIR):
        os.makedirs(COMPOSE_DIR)

@router.get("/projects")
async def list_projects():
    ensure_compose_dir()
    projects = []
    for d in os.listdir(COMPOSE_DIR):
        path = os.path.join(COMPOSE_DIR, d)
        if os.path.isdir(path):
            projects.append({"name": d, "path": path})
    return projects

@router.get("/projects/{name}")
async def get_project(name: str):
    file_path = os.path.join(COMPOSE_DIR, name, "docker-compose.yml")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Project not found")
    with open(file_path, "r") as f:
        content = f.read()
    return {"name": name, "content": content}

@router.post("/projects")
async def save_project(project: ComposeProject):
    start_time = time.time()
    logger.info(f"💾 [Compose] 正在保存项目配置: {project.name}")
    project_dir = os.path.join(COMPOSE_DIR, project.name)
    os.makedirs(project_dir, exist_ok=True)
    file_path = os.path.join(project_dir, "docker-compose.yml")
    with open(file_path, "w") as f:
        f.write(project.content)
    
    logger.info(f"✅ [Compose] 项目 {project.name} 配置已写入: {file_path}")
    audit_log(f"Compose Project Saved", (time.time() - start_time) * 1000, [f"Name: {project.name}"])
    return {"message": "Project saved"}

@router.delete("/projects/{name}")
async def delete_project(name: str):
    logger.warning(f"🗑️ [Compose] 正在删除项目: {name}")
    project_dir = os.path.join(COMPOSE_DIR, name)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    logger.info(f"✅ [Compose] 项目 {name} 已彻底移除")
    return {"message": "Project deleted"}

@router.post("/projects/{name}/action")
async def project_action(name: str, action: str = Body(..., embed=True)):
    start_time = time.time()
    logger.info(f"🛠️ [Compose] 收到项目操作请求: 动作={action}, 项目={name}")
    project_dir = os.path.join(COMPOSE_DIR, name)
    if not os.path.exists(project_dir):
        logger.error(f"❌ [Compose] 操作失败: 项目目录不存在 -> {project_dir}")
        raise HTTPException(status_code=404, detail="Project directory not found")

    # 自动探测可用命令
    import shutil
    if shutil.which("docker") and subprocess.run(["docker", "compose", "version"], capture_output=True).returncode == 0:
        base_cmd = ["docker", "compose"]
    elif shutil.which("docker-compose"):
        base_cmd = ["docker-compose"]
    else:
        logger.error("❌ [Compose] 未找到 docker compose 或 docker-compose 命令")
        raise HTTPException(status_code=500, detail="未在容器内找到 docker compose 命令。")

    commands = {
        "up": base_cmd + ["up", "-d"],
        "down": base_cmd + ["down"],
        "pull": base_cmd + ["pull"],
        "restart": base_cmd + ["restart"]
    }

    if action not in commands:
        raise HTTPException(status_code=400, detail="Invalid action")

    try:
        logger.info(f"⚙️ [Compose] 正在执行命令: {' '.join(commands[action])}")
        process = subprocess.Popen(
            commands[action],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            logger.info(f"✅ [Compose] 项目 {name} 操作完成: {action}")
        else:
            logger.error(f"❌ [Compose] 项目 {name} 操作失败 (code={process.returncode})")
        
        audit_log(f"Compose Action: {action}", (time.time() - start_time) * 1000, [f"Project: {name}"])
        
        return {
            "success": process.returncode == 0,
            "stdout": stdout,
            "stderr": stderr
        }
    except Exception as e:
        logger.error(f"🚨 [Compose] 系统级错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
