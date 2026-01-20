from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import router as api_router
from app.utils.logger import logger, log_queue, audit_log
from app.db.session import engine, Base
from app.models import * # 确保所有模型都被 Base 注册
import asyncio
import os
import time

# 确保数据目录存在
os.makedirs("/app/data", exist_ok=True)

app = FastAPI(
    title="EmbyLens API",
    description="Emby 媒体库管理与去重工具后端",
    version="1.0.5"
)

# 全局性能审计中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # 排除高频且无意义的系统级审计，防止日志循环刷屏
    exclude_paths = [
        "/api/system/logs", 
        "/api/stats/summary", 
        "/api/status",
        "/api/docker", # 彻底排除所有 Docker 相关接口的审计日志
        "/api/pgsql"   # 彻底排除所有 PostgreSQL 相关接口的审计日志
    ]
    
    should_audit = request.url.path.startswith("/api") and not any(p in request.url.path for p in exclude_paths)

    if should_audit:
        audit_log(f"API {request.method} {request.url.path}", process_time, [
            f"Status: {response.status_code}",
            f"Client: {request.client.host if request.client else 'unknown'}"
        ])
    return response

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # 自动创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 强制禁用 SSH 主机密钥检查，解决 Docker SSH 连接 known_hosts 问题
    try:
        ssh_config_dir = os.path.expanduser("~/.ssh")
        os.makedirs(ssh_config_dir, exist_ok=True)
        config_path = os.path.join(ssh_config_dir, "config")
        with open(config_path, "w") as f:
            f.write("Host *\n    StrictHostKeyChecking no\n    UserKnownHostsFile /dev/null\n")
        os.chmod(config_path, 0o600)
    except Exception as e:
        logger.error(f"Failed to setup SSH config: {e}")
    
    # 启动自动标签 Webhook 消费 Worker
    from app.api.autotags import webhook_worker
    asyncio.create_task(webhook_worker())
    
    audit_log("系统启动", 120, [
        "数据库表结构已初始化",
        "持久化目录: /app/data",
        "日志系统就绪",
        "端口: 6565"
    ])

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
        # 排除 API 路径
        if full_path.startswith("api"):
            return None
        
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
        return {"message": "EmbyLens API is running. Frontend static files not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=6565, reload=True)
