from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt
import bcrypt
import os
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.services.config_service import ConfigService

# 加密配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "lens_secret_key_change_me_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 默认登录有效期 24 小时

def verify_password(plain_password: str, hashed_password: str):
    """校验明文密码与哈希值是否匹配"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str):
    """对明文密码进行加密"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """解析并验证 JWT 令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """获取当前用户的依赖项"""
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
                return user

    if not ui_auth_enabled:
        # 如果未开启认证，返回默认管理员
        result = await db.execute(select(User).where(User.username == "admin"))
        return result.scalars().first()
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )