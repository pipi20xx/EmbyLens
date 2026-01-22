from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import router as api_router
from app.utils.logger import logger, log_queue, audit_log
from sqlalchemy import select
from app.db.session import engine, Base, get_db
from app.models import * 
from app.models.user import User
from app.utils.auth import get_password_hash
from app.utils.audit import add_audit_log, mask_sensitive_data
from app.services.config_service import ConfigService
import asyncio
import os
import time
import json

# 确保数据目录存在
os.makedirs("/app/data/nav_icons", exist_ok=True)
os.makedirs("/app/data/logs/audit", exist_ok=True)

app = FastAPI(
    title="Lens API",
    description="Lens 媒体库管理系统后端 API",
    version="2.0.6",
    docs_url=None, 
    redoc_url=None
)

# 全局审计与性能监控中间件
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 排除审计路径和文件上传路径
    exclude_paths = [
        "/api/system/logs", 
        "/api/stats/summary", 
        "/api/status",
        "/api/auth/status",
        "/api/system/config",
        "/api/system/version",
        "/api/system/audit/logs",
        "/api/docker",
        "/api/pgsql",
        "/api/navigation",
        "/ws/"
    ]
    
    is_api = request.url.path.startswith("/api")
    is_excluded = any(p in request.url.path for p in exclude_paths)
    is_upload = "multipart/form-data" in request.headers.get("content-type", "")

    # 捕获请求体 (仅针对非 GET 且非上传、非排除路径的请求)
    payload_str = None
    if request.method != "GET" and is_api and not is_excluded and not is_upload:
        try:
            body = await request.body()
            if body:
                try:
                    payload_str = body.decode("utf-8")
                    # 重新包装 request 以允许下游继续读取 body
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
                except UnicodeDecodeError:
                    payload_str = "[Binary Data]"
        except Exception:
            pass
    
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    should_audit = is_api and not is_excluded

    if should_audit:
        # 执行脱敏处理
        masked_payload = payload_str
        if payload_str:
            try:
                payload_json = json.loads(payload_str)
                masked_json = await mask_sensitive_data(payload_json)
                masked_payload = json.dumps(masked_json, ensure_ascii=False)
            except:
                pass

        # 记录到 JSON 审计日志
        asyncio.create_task(add_audit_log(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            client_ip=request.client.host if request.client else "unknown",
            process_time=process_time,
            query_params=str(request.query_params),
            payload=masked_payload
        ))
        
        # 记录到控制台性能审计
        audit_log(f"API {request.method} {request.url.path}", process_time, [
            f"Status: {response.status_code}",
            f"Client: {request.client.host if request.client else 'unknown'}"
        ])
        
    return response

@app.on_event("startup")
async def startup_event():
    # 自动创建数据库表并执行自愈修复
    from app.utils.db_repair import init_db_with_repair
    await init_db_with_repair(engine)
    
    # 启动备份任务调度器
    from app.services.backup_service import BackupService
    asyncio.create_task(BackupService.start_scheduler())
    
    # 初始化默认管理员
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalars().first():
            admin_user = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True
            )
            db.add(admin_user)
            await db.commit()
            logger.info("默认管理员账户已创建 (admin/admin123)")

    # 初始化系统默认配置 (优先从 config.json 加载)
    from app.core.config_manager import get_config
    current_json_config = get_config()
    
    default_configs = [
        {"key": "ui_auth_enabled", "value": "true", "description": "是否开启前端页面登录校验"},
        {"key": "audit_enabled", "value": "true", "description": "是否开启全局 API 审计日志"},
        {"key": "api_token", "value": "", "description": "外部 API 调用 Token"}
    ]
    for cfg in default_configs:
        # 强制同步核心配置项：如果 config.json 里有，以 config.json 为准覆盖数据库
        if cfg["key"] in current_json_config and current_json_config[cfg["key"]]:
            val = current_json_config[cfg["key"]]
            await ConfigService.set(cfg["key"], val, cfg["description"])
        else:
            # 否则仅在数据库缺失时初始化
            current_val = await ConfigService.get(cfg["key"])
            if current_val is None:
                await ConfigService.set(cfg["key"], cfg["value"], cfg["description"])

    # 强制禁用 SSH 主机密钥检查


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("正在关闭服务...")
    logger.info("[系统] 服务已安全关闭。")

# WebSocket 实时日志
@app.websocket("/ws/system/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # 获取最近的历史日志并回填
    from app.utils.logger import get_last_n_logs
    history = get_last_n_logs(200) # 增加回填行数到 200
    history.reverse() # 反转，确保最新的一条最先发出（配合前端 unshift）
    for line in history:
        try:
            await websocket.send_text(line)
        except:
            return

    try:
        while True:
            # 获取队列中的新日志
            msg = await log_queue.get()
            try:
                await websocket.send_text(msg)
            except Exception:
                # 如果发送失败（连接已关），直接退出
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# ... (其他导入)

# 挂载图标目录
os.makedirs("/app/data/nav_icons", exist_ok=True)
os.makedirs("/app/data/nav_backgrounds", exist_ok=True)
app.mount("/nav_icons", StaticFiles(directory="/app/data/nav_icons"), name="nav_icons")
app.mount("/nav_backgrounds", StaticFiles(directory="/app/data/nav_backgrounds"), name="nav_backgrounds")

# 包含 API 路由
app.include_router(api_router, prefix="/api")

# --- 快捷图标路由 (解决第三方工具抓取失败问题) ---
@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.svg", include_in_schema=False)
async def favicon():
    icon_path = os.path.join("./static", "favicon.svg")
    if os.path.exists(icon_path):
        return FileResponse(icon_path, media_type="image/svg+xml")
    return None

# 托管静态文件 (前端)
if os.path.exists("./static"):
    # 静态资源目录 (JS, CSS, Images)
    @app.get("/assets/{file_path:path}")
    async def serve_assets(file_path: str):
        file_full_path = os.path.join("./static/assets", file_path)
        if os.path.exists(file_full_path):
            return FileResponse(file_full_path)
        return None

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # 排除 API、图标和背景缓存路径
        if full_path.startswith("api") or full_path.startswith("nav_icons") or full_path.startswith("nav_backgrounds"):
            raise HTTPException(status_code=404)
        
        # 检查是否是具体的文件请求（比如 /vite.svg）
        file_path = os.path.join("./static", full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # SPA 路由兜底：返回 index.html
        index_path = os.path.join("./static", "index.html")
        return FileResponse(index_path)
else:
    @app.get("/")
    async def root():
        return {"message": "Lens API is running. Frontend static files not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=6565, reload=True)
