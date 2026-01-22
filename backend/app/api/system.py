from fastapi import APIRouter, Query, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.session import get_db
from app.models.config import SystemConfig
from app.schemas.system import BatchConfigUpdate, AuditLogListResponse, AuditLogResponse
from app.services.config_service import ConfigService
from app.utils.logger import get_log_dates, get_log_content, LOG_DIR, logger
from app.utils.http_client import get_async_client
from app.services.docker_service import DockerService
from app.core.config_manager import get_config
from datetime import datetime
import os
import secrets
import asyncio

router = APIRouter()

CURRENT_VERSION = "v2.0.6"
DOCKER_IMAGE = "pipi20xx/lens"

@router.get("/version")
async def check_version():
    """检测 Docker Hub 上的最新版本"""
    # 统一处理本地版本号，移除可能存在的 v 前缀
    local_ver = CURRENT_VERSION.lstrip('v').strip()
    latest_version = local_ver
    has_update = False
    
    try:
        # 使用配置了代理的客户端
        url = f"https://hub.docker.com/v2/repositories/{DOCKER_IMAGE}/tags/?page_size=5&ordering=last_updated"
        async with get_async_client(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                tags = data.get("results", [])
                
                for tag in tags:
                    tag_name = tag.get("name")
                    if tag_name and tag_name != "latest":
                        # 统一移除远程版本号的 v 前缀进行比较
                        remote_ver = tag_name.lstrip('v').strip()
                        latest_version = remote_ver
                        
                        # 如果远程版本不等于本地版本
                        if remote_ver != local_ver:
                            # 简单的字符串大小比较或拆分比较
                            try:
                                remote_parts = [int(p) for p in remote_ver.split('.')]
                                local_parts = [int(p) for p in local_ver.split('.')]
                                if remote_parts > local_parts:
                                    has_update = True
                            except:
                                # 如果解析失败，回退到简单的非等比较
                                if remote_ver != local_ver:
                                    has_update = True
                        break
    except Exception:
        pass

    return {
        "current": f"v{local_ver}",
        "latest": f"v{latest_version}",
        "has_update": has_update,
        "docker_hub": f"https://hub.docker.com/r/{DOCKER_IMAGE}"
    }

@router.post("/upgrade")
async def upgrade_system(host_id: str = Query(None)):
    """一键系统升级：执行在被标记为 is_local 的宿主机上"""
    config = get_config()
    hosts = config.get("docker_hosts", [])
    
    target_host = None
    
    # 1. 寻找被用户手动标记为宿主机的节点
    if host_id:
        target_host = next((h for h in hosts if h.get("id") == host_id), None)
    else:
        # 寻找 is_local 为 True 的主机
        target_host = next((h for h in hosts if h.get("is_local") is True), None)

    if not target_host:
        raise HTTPException(
            status_code=400, 
            detail="升级中断：未找到标记为“宿主机”的连接。请在“Docker 容器管理”中编辑你的宿主机连接，并开启“宿主机标记”开关。"
        )

    try:
        service = DockerService(target_host)
        
        # 获取当前容器短 ID 用于探测路径
        import socket
        my_id = socket.gethostname()
        
        # 自动探测物理路径
        inspect_cmd = f"docker inspect {my_id} --format '{{{{json .Mounts}}}}'"
        res = service.exec_command(inspect_cmd)
        
        project_path = None
        if res["success"]:
            try:
                import json
                mounts = json.loads(res["stdout"])
                for m in mounts:
                    if m.get("Destination") == "/app/data":
                        project_path = os.path.dirname(m.get("Source"))
                        break
            except: pass

        if not project_path:
            project_path = target_host.get("project_path") or "/vol1/1000/NVME/Lens"
            logger.warning(f"⚠️ [系统升级] 路径探测失败，使用回退路径: {project_path}")

        # 执行升级命令
        upgrade_cmd = (
            f"(cd {project_path} && "
            "git pull && "
            "docker compose up -d --build) > {project_path}/data/logs/upgrade.log 2>&1 &"
        )
        
        logger.info(f"🚀 [系统升级] 用户已授权，正在通过宿主机 {target_host.get('name')} 执行后台升级...")
        res = service.exec_command(upgrade_cmd)
        
        if res["success"]:
            return {
                "message": f"升级任务已在宿主机 {target_host.get('name')} 上启动！系统正在拉取代码并重新构建，请稍后刷新页面。",
                "detected_path": project_path
            }
        else:
            raise HTTPException(status_code=500, detail=f"升级脚本启动失败: {res['stderr']}")
            
    except Exception as e:
        logger.error(f"❌ [系统升级] 发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/docs", include_in_schema=False)
async def get_documentation(request: Request, theme: str = "purple", token: str = None):
    referer = request.headers.get("referer")
    host = request.headers.get("host")
    
    # 允许 localhost 访问，或检查 referer
    if referer and host not in referer and "localhost" not in referer:
         raise HTTPException(status_code=403, detail="禁止直接访问 API 文档。请通过系统仪表盘进入。")
    
    # 根据主题定义配色
    primary_color = "#bb86fc" if theme == "purple" else "#705df2"
    bg_color = "#0b040f" if theme == "purple" else "#101014"
    card_bg = "#180a20" if theme == "purple" else "#1e1e24"
    text_color = "#e0e0e0"

    # 自动授权脚本
    auth_js = ""
    if token:
        auth_js = f"""
        setTimeout(function() {{
            if (window.ui) {{
                window.ui.authActions.authorize({{
                    "BearerAuth": {{
                        name: "BearerAuth",
                        schema: {{
                            type: "http",
                            scheme: "bearer",
                            bearerFormat: "JWT"
                        }},
                        value: "{token}"
                    }}
                }});
                console.log("Lens：API Token 已自动注入");
            }}
        }}, 1000);
        """

    custom_css = f"""
    /* 基础背景与文字 */
    body {{ background-color: {bg_color} !important; margin: 0; padding: 0; }}
    .swagger-ui {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    
    .swagger-ui .topbar {{ display: none; }}
    .swagger-ui .info .title, .swagger-ui .info li, .swagger-ui .info p, .swagger-ui .info table, .swagger-ui .info h1, .swagger-ui .info h2, .swagger-ui .info h3 {{ color: {text_color} !important; }}
    
    /* 接口区块与标签 */
    .swagger-ui .opblock-tag {{ color: {text_color} !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; }}
    .swagger-ui .opblock-tag:hover {{ background: rgba(255,255,255,0.05) !important; }}
    .swagger-ui .opblock {{ background: {card_bg} !important; border: 1px solid rgba(255,255,255,0.05) !important; box-shadow: none !important; }}
    .swagger-ui .opblock .opblock-summary-path {{ color: {text_color} !important; }}
    .swagger-ui .opblock .opblock-summary-description {{ color: rgba(255,255,255,0.6) !important; }}
    
    /* 参数与请求配置区 */
    .swagger-ui .scheme-container {{ background: {card_bg} !important; box-shadow: none !important; border-top: 1px solid rgba(255,255,255,0.05) !important; }}
    .swagger-ui select {{ background: {bg_color} !important; color: {text_color} !important; border-color: rgba(255,255,255,0.2) !important; }}
    .swagger-ui input {{ background: {card_bg} !important; color: {text_color} !important; border: 1px solid rgba(255,255,255,0.1) !important; }}
    .swagger-ui .btn {{ color: {text_color} !important; border-color: rgba(255,255,255,0.2) !important; background: transparent !important; }}
    .swagger-ui .btn.execute {{ background-color: {primary_color} !important; border-color: {primary_color} !important; color: #000 !important; font-weight: bold !important; }}
    
    /* 重点：授权弹窗 (Available authorizations) 适配 */
    .swagger-ui .modal-ux {{ background-color: {bg_color} !important; border: 1px solid rgba(255,255,255,0.1) !important; }}
    .swagger-ui .modal-ux-header {{ border-bottom: 1px solid rgba(255,255,255,0.1) !important; }}
    .swagger-ui .modal-ux-header h3 {{ color: {text_color} !important; }}
    .swagger-ui .modal-ux-content {{ background-color: {bg_color} !important; }}
    .swagger-ui .modal-ux-content h4 {{ color: {text_color} !important; }}
    .swagger-ui .auth-container {{ color: {text_color} !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; }}
    .swagger-ui .auth-container:last-of-type {{ border-bottom: none !important; }}
    .swagger-ui .auth-container label {{ color: {text_color} !important; }}
    .swagger-ui .auth-btn-wrapper {{ justify-content: center !important; gap: 10px !important; }}
    .swagger-ui .modal-ux-content p {{ color: rgba(255,255,255,0.6) !important; }}
    .swagger-ui .authorization__btn svg {{ fill: {primary_color} !important; }}

    /* 参数 (Parameters) 与交互区适配 */
    .swagger-ui .opblock-section-header {{ background: rgba(255,255,255,0.05) !important; border-top: 1px solid rgba(255,255,255,0.1) !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; }}
    .swagger-ui .opblock-section-header h4 {{ color: {text_color} !important; }}
    .swagger-ui table.parameters thead th {{ color: {text_color} !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; }}
    .swagger-ui .parameter__name {{ color: {primary_color} !important; font-weight: bold !important; }}
    .swagger-ui .parameter__type {{ color: #f2a3ff !important; }}
    .swagger-ui .parameter__in {{ font-style: italic !important; color: rgba(255,255,255,0.5) !important; }}
    
    /* 按钮适配 */
    .swagger-ui .btn.try-out__btn {{ border-color: {primary_color} !important; color: {primary_color} !important; transition: all 0.3s !important; }}
    .swagger-ui .btn.try-out__btn:hover {{ background-color: rgba(255,255,255,0.05) !important; }}
    .swagger-ui .btn.try-out__btn.cancel {{ border-color: #ff5252 !important; color: #ff5252 !important; }}
    
    /* 响应结果区 */
    .swagger-ui .responses-inner h4, .swagger-ui .responses-inner h5 {{ color: {text_color} !important; }}
    .swagger-ui .response-col_status {{ color: {text_color} !important; font-weight: bold !important; }}
    .swagger-ui .opblock-body pre {{ background: #111 !important; color: #70ff70 !important; border: 1px solid rgba(255,255,255,0.1) !important; padding: 10px !important; border-radius: 8px !important; }}
    
    /* 模型 (Models) 适配 */
    .swagger-ui .model-box {{ background: transparent !important; }}
    .swagger-ui .model {{ color: {text_color} !important; }}
    .swagger-ui section.models .model-container {{ background: {card_bg} !important; border: 1px solid rgba(255,255,255,0.05) !important; margin-bottom: 10px !important; }}
    .swagger-ui section.models h4 {{ color: {text_color} !important; }}
    .swagger-ui .model-title {{ color: {text_color} !important; }}
    .swagger-ui .prop-name {{ color: {text_color} !important; font-weight: bold !important; }}
    .swagger-ui .prop-type {{ color: #f2a3ff !important; }}
    """
    
    from fastapi.openapi.docs import get_swagger_ui_html
    response = get_swagger_ui_html(
        openapi_url="/api/system/openapi.json", 
        title="Lens API Documentation"
    )
    
    html_content = response.body.decode("utf-8")
    custom_injection = f"<style>{custom_css}</style><script>{auth_js}</script>"
    new_content = html_content.replace("</head>", f"{custom_injection}</head>")
    
    return HTMLResponse(content=new_content)

@router.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(request: Request):
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(title="Lens API", version=CURRENT_VERSION, routes=request.app.routes)
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    return schema

@router.get("/config", summary="获取所有系统配置")
async def get_all_configs(db: AsyncSession = Depends(get_db)):
    # 1. 获取数据库中的所有配置项
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    res = {c.key: c.value for c in configs}
    
    # 2. 确保关键配置项（如 api_token）通过 ConfigService 获取（包含 config.json 的回退逻辑）
    keys_to_ensure = ["api_token", "ui_auth_enabled", "audit_enabled"]
    for key in keys_to_ensure:
        if key not in res or not res[key]:
            res[key] = await ConfigService.get(key)
            
    return res

@router.post("/config", summary="批量更新系统配置")
async def update_configs(update: BatchConfigUpdate):
    for cfg in update.configs:
        await ConfigService.set(cfg.key, cfg.value, cfg.description)
    return {"message": "配置已更新"}

@router.post("/token/generate", summary="生成随机 API Token")
async def generate_token():
    token = secrets.token_urlsafe(32)
    return {"token": token}

@router.get("/audit/logs", response_model=AuditLogListResponse, summary="查询审计日志")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    from app.utils.audit import audit_buffer
    total = len(audit_buffer)
    start = (page - 1) * page_size
    end = start + page_size
    items = audit_buffer[start:end]
    return {"total": total, "items": items}

@router.get("/logs/dates")
async def fetch_log_dates():
    return get_log_dates()

@router.get("/logs/content/{date}")

async def fetch_log_content(date: str):

    # 返回原始顺序，由前端 LogConsole 处理反转

    return {"content": get_log_content(date)}



@router.get("/logs/raw", response_class=PlainTextResponse)

async def fetch_raw_log(type: str = Query("monitor")):

    """日志接口：返回当前最新的原始文本日志 (倒序，最新在上)"""

    current_date = datetime.now().strftime("%Y-%m-%d")

    content = get_log_content(current_date)

    lines = content.splitlines()

    lines.reverse()

    return "\n".join(lines)



@router.get("/logs/export/{date}", response_class=PlainTextResponse)

async def export_log_by_date(date: str):

    """按日期返回原始文本日志 (倒序，最新在上)"""

    content = get_log_content(date)

    lines = content.splitlines()

    lines.reverse()

    return "\n".join(lines)


