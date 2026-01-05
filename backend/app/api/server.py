from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import httpx
import uuid
import time
from app.core.config_manager import get_config, save_config
from app.services.emby import EmbyService
from app.utils.logger import logger
from app.utils.http_client import get_async_client

router = APIRouter()

@router.post("/test")
async def test_connection(config: Dict[str, Any]):
    service = EmbyService(config.get("url", ""), config.get("api_key", ""))
    success = await service.test_connection()
    if not success:
        raise HTTPException(status_code=400, detail="无法连接到 Emby 服务器")
    return {"message": "连接成功"}

@router.post("/save")
async def save_server_config(config: Dict[str, Any]):
    """保存配置到 config.json"""
    # 保持 session_token 不被覆盖（如果前端没传的话）
    current = get_config()
    if "session_token" not in config and "session_token" in current:
        config["session_token"] = current["session_token"]
    
    save_config(config)
    return config

@router.get("/current")
async def get_current_config():
    """获取当前 config.json 内容"""
    return get_config()

@router.post("/login")
async def emby_login():
    """使用 config.json 中的凭据登录并获取 Session Token"""
    config = get_config()
    url = config.get("url", "").strip().rstrip('/')
    username = config.get("username", "").strip()
    password = config.get("password", "").strip()
    
    if not url or not username:
        raise HTTPException(status_code=400, detail="未配置服务器地址或用户名")

    if url.endswith('/emby'):
        url = url[:-5]

    try:
        auth_url = f"{url}/emby/Users/AuthenticateByName"
        device_id = str(uuid.uuid4())
        auth_header = f'MediaBrowser Client="EmbyLens", Device="Server", DeviceId="{device_id}", Version="1.0.0"'
        
        proxy_cfg = config.get("proxy", {})
        use_proxy = not proxy_cfg.get("exclude_emby", True)

        async with get_async_client(timeout=15, use_proxy=use_proxy) as client:
            resp = await client.post(
                auth_url,
                json={"Username": username, "Pw": password or ""},
                headers={"X-Emby-Authorization": auth_header}
            )
            resp.raise_for_status()
            data = resp.json()
            token = data.get("AccessToken")
            user_id = data.get("User", {}).get("Id")
            
            if token:
                config["session_token"] = token
                if user_id: config["user_id"] = user_id
                save_config(config)
                return {"message": "登录成功", "token": token}
            
            raise ValueError("登录成功但未收到令牌")
    except Exception as e:
        logger.error(f"Emby 登录失败: {e}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

@router.get("/libraries")
async def get_emby_libraries():
    config = get_config()
    url = config.get("url")
    api_key = config.get("api_key")
    
    if not url or not api_key:
        return []
    
    service = EmbyService(url, api_key)
    try:
        # 使用 service._request 内部封装的逻辑，它会自动处理 api_key 和超时
        resp = await service._request("GET", "/Library/VirtualFolders")
        if resp and resp.status_code == 200:
            folders = resp.json()
            return [{"label": f["Name"], "value": f["Name"]} for f in folders]
        return []
    except Exception as e:
        logger.error(f"获取媒体库失败: {e}")
        return []
