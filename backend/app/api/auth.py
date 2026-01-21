from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.utils.auth import verify_password, create_access_token, decode_access_token, get_password_hash
from app.utils.audit import add_audit_log
from app.utils.time import get_local_time
from app.schemas.auth import LoginRequest, PasswordChangeRequest, TokenResponse
from app.services.config_service import ConfigService
from datetime import timedelta
import asyncio
import pyotp
import qrcode
import io
import base64

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

@router.post("/login", response_model=TokenResponse, summary="管理员登录")
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    from app.utils.rate_limit import login_limiter
    client_ip = request.client.host if request.client else "unknown"
    
    is_locked, remaining = login_limiter.is_locked(client_ip)
    if is_locked:
        raise HTTPException(status_code=429, detail=f"封锁中，请在 {remaining} 秒后再试")

    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalars().first()
    
    if not user or not verify_password(req.password, user.hashed_password):
        login_limiter.record_failure(client_ip)
        asyncio.create_task(add_audit_log("POST", "/api/auth/login", 401, client_ip, 0, payload=f"登录失败: {req.username}"))
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if user.is_otp_enabled:
        if not req.otp_code:
            pending_token = create_access_token(data={"sub": user.username, "type": "2fa_pending"}, expires_delta=timedelta(minutes=5))
            return {
                "access_token": pending_token,
                "token_type": "bearer",
                "username": user.username,
                "status": "2fa_required"
            }
        totp = pyotp.TOTP(user.otp_secret)
        if not totp.verify(req.otp_code):
            login_limiter.record_failure(client_ip)
            raise HTTPException(status_code=401, detail="2FA 验证码错误")

    login_limiter.reset(client_ip)
    user.last_login = get_local_time()
    await db.commit()
    
    access_token = create_access_token(data={"sub": user.username})
    asyncio.create_task(add_audit_log("POST", "/api/auth/login", 200, client_ip, 0, payload=f"登录成功: {user.username}"))
    
    return {"access_token": access_token, "token_type": "bearer", "username": user.username, "status": "success"}

@router.post("/password", summary="修改管理员密码")
async def change_password(req: PasswordChangeRequest, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=401)
    username = payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not verify_password(req.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="旧密码错误")
    user.hashed_password = get_password_hash(req.new_password)
    await db.commit()
    asyncio.create_task(add_audit_log("POST", "/api/auth/password", 200, "internal", 0, payload=f"用户 {username} 修改密码"))
    return {"message": "成功"}

@router.get("/2fa/setup", summary="获取 2FA 设置信息")
async def setup_2fa(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=401)
    username = payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    secret = pyotp.random_base32()
    user.otp_secret = secret
    await db.commit()
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="EmbyLens")
    img = qrcode.make(totp_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return {"secret": secret, "qr_code": f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"}

@router.post("/2fa/enable", summary="正式开启 2FA")
async def enable_2fa(code: str, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=401)
    username = payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if pyotp.TOTP(user.otp_secret).verify(code):
        user.is_otp_enabled = True
        await db.commit()
        return {"message": "成功"}
    raise HTTPException(status_code=400, detail="码无效")

@router.post("/2fa/disable", summary="关闭 2FA")
async def disable_2fa(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=401)
    username = payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    user.is_otp_enabled = False
    await db.commit()
    return {"message": "成功"}

@router.get("/status", summary="获取系统认证状态")
async def get_auth_status():
    val = await ConfigService.get("ui_auth_enabled", True)
    # 强制转换为真正的 Python bool，确保 JSON 输出为 true/false 而非 "true"/"false"
    ui_auth_enabled = val is True or str(val).lower() == "true"
    return {"ui_auth_enabled": ui_auth_enabled}

@router.get("/me", summary="获取当前用户信息")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    # 检查是否开启了 UI 认证
    ui_auth_enabled_val = await ConfigService.get("ui_auth_enabled", True)
    ui_auth_enabled = ui_auth_enabled_val is True or str(ui_auth_enabled_val).lower() == "true"
    
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "") if auth_header and auth_header.startswith("Bearer ") else None
    
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("type") != "2fa_pending":
            username = payload.get("sub")
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            if user:
                return {"username": user.username, "is_otp_enabled": user.is_otp_enabled, "last_login": user.last_login}

    if not ui_auth_enabled:
        return {"username": "admin (免密模式)", "is_otp_enabled": False, "last_login": None}
    
    raise HTTPException(status_code=401, detail="Not authenticated")
