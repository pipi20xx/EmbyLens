from fastapi import APIRouter, HTTPException, Body
from typing import Optional, Dict, Any, List
import httpx
import uuid
import time
from app.core.config_manager import get_config, save_config
from app.services.emby import EmbyService, get_emby_service
from app.utils.logger import logger
from app.utils.http_client import get_async_client

router = APIRouter()

@router.get("/list")
async def list_servers():
    """获取所有 Emby 服务器列表"""
    config = get_config()
    return {
        "servers": config.get("emby_servers", []),
        "active_id": config.get("active_server_id")
    }

@router.post("/activate/{server_id}")
async def activate_server(server_id: str):
    """切换当前激活的 Emby 服务器"""
    config = get_config()
    servers = config.get("emby_servers", [])
    if not any(s.get("id") == server_id for s in servers):
        raise HTTPException(status_code=404, detail="服务器不存在")
    
    config["active_server_id"] = server_id
    save_config(config)
    return {"message": "切换成功", "active_id": server_id}

@router.delete("/{server_id}")
async def delete_server(server_id: str):
    """删除指定的 Emby 服务器"""
    config = get_config()
    servers = config.get("emby_servers", [])
    new_servers = [s for s in servers if s.get("id") != server_id]
    
    if len(new_servers) == len(servers):
        raise HTTPException(status_code=404, detail="服务器不存在")
        
    config["emby_servers"] = new_servers
    # 如果删除的是当前激活的，则重置激活 ID
    if config.get("active_server_id") == server_id:
        config["active_server_id"] = new_servers[0].get("id") if new_servers else ""
        
    save_config(config)
    return {"message": "删除成功"}

@router.post("/test")
async def test_connection(config: Dict[str, Any]):
    service = EmbyService(config.get("url", ""), config.get("api_key", ""))
    info = await service.test_connection()
    if not info:
        raise HTTPException(status_code=400, detail="无法连接到 Emby 服务器")
    return {"message": "连接成功", "server_id": info.get("Id"), "server_name": info.get("ServerName")}

@router.post("/save")
async def save_server_config(config: Dict[str, Any]):
    """保存配置 (支持新增或更新特定服务器，或仅更新全局配置)"""
    full_config = get_config()
    
    # 提取 Emby 服务器相关的字段
    emby_fields = ["id", "name", "url", "api_key", "user_id", "username", "password", "session_token", "emby_id"]
    server_data = {k: v for k, v in config.items() if k in emby_fields}
    
    # 逻辑修正：只有当明确提供了服务器 ID，或者提供了核心连接信息（URL + API Key）时，才处理服务器列表
    is_server_op = server_data.get("id") or (server_data.get("url") and server_data.get("api_key"))
    
    if is_server_op:
        # 尝试获取真实的 Emby ID
        if server_data.get("url") and server_data.get("api_key"):
            try:
                service = EmbyService(server_data["url"], server_data["api_key"])
                info = await service.test_connection()
                if info:
                    server_data["emby_id"] = info.get("Id")
                    if not server_data.get("name"):
                        server_data["name"] = info.get("ServerName")
            except:
                pass
        
        # 如果有 ID，则是更新；否则是新增
        if server_data.get("id"):
            servers = full_config.get("emby_servers", [])
            found = False
            for i, s in enumerate(servers):
                if s.get("id") == server_data["id"]:
                    servers[i].update(server_data)
                    found = True
                    break
            if not found:
                servers.append(server_data)
        else:
            server_data["id"] = str(uuid.uuid4())
            if "emby_servers" not in full_config:
                full_config["emby_servers"] = []
            full_config["emby_servers"].append(server_data)
            # 如果是第一个服务器，自动激活
            if not full_config.get("active_server_id"):
                full_config["active_server_id"] = server_data["id"]

    # 更新非 Emby 服务器字段 (如代理、API Key 等全局配置)
    for key, value in config.items():
        if key not in emby_fields:
            full_config[key] = value
    
    save_config(full_config)
    return full_config

@router.get("/current")
async def get_current_config():
    """获取当前激活的服务器配置及全局设置"""
    config = get_config()
    active_id = config.get("active_server_id")
    servers = config.get("emby_servers", [])
    
    active_server = next((s for s in servers if s.get("id") == active_id), {})
    
    # 合并全局配置与激活的服务器配置返回给前端
    result = config.copy()
    result.update(active_server)
    return result

@router.post("/login")
async def emby_login(server_id: Optional[str] = Body(None, embed=True)):
    """使用指定或当前激活服务器的凭据登录"""
    config = get_config()
    
    target_server = None
    if server_id:
        target_server = next((s for s in config.get("emby_servers", []) if s.get("id") == server_id), None)
    else:
        active_id = config.get("active_server_id")
        target_server = next((s for s in config.get("emby_servers", []) if s.get("id") == active_id), None)
        
    if not target_server:
        raise HTTPException(status_code=400, detail="未找到服务器配置")

    url = target_server.get("url", "").strip().rstrip('/')
    username = target_server.get("username", "").strip()
    password = target_server.get("password", "").strip()
    
    if not url or not username:
        raise HTTPException(status_code=400, detail="未配置服务器地址或用户名")

    if url.endswith('/emby'):
        url = url[:-5]

    try:
        auth_url = f"{url}/emby/Users/AuthenticateByName"
        device_id = str(uuid.uuid4())
        auth_header = f'MediaBrowser Client="Lens", Device="Server", DeviceId="{device_id}", Version="1.0.0"'
        
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
                # 更新到列表中的特定服务器
                for s in config["emby_servers"]:
                    if s["id"] == target_server["id"]:
                        s["session_token"] = token
                        if user_id: s["user_id"] = user_id
                        break
                save_config(config)
                return {"message": "登录成功", "token": token}
            
            raise ValueError("登录成功但未收到令牌")
    except Exception as e:
        logger.error(f"Emby 登录失败: {e}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

@router.get("/libraries")
async def get_emby_libraries():
    service = get_emby_service()
    if not service:
        return []
    
    try:
        resp = await service._request("GET", "/Library/VirtualFolders")
        if resp and resp.status_code == 200:
            folders = resp.json()
            return [{"label": f["Name"], "value": f["Name"]} for f in folders]
        return []
    except Exception as e:
        logger.error(f"获取媒体库失败: {e}")
        return []
