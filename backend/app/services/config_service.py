from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.config import SystemConfig
from typing import Optional, Any
import asyncio

class ConfigService:
    _cache = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get(cls, key: str, default: Any = None) -> Any:
        async with cls._lock:
            if key in cls._cache:
                return cls._cache[key]

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(SystemConfig).where(SystemConfig.key == key))
            config = result.scalars().first()
            val = config.value if config else None
            
            # 如果数据库没有，尝试从 config.json 获取 (Lens 规范)
            if val is None:
                try:
                    from app.core.config_manager import get_config
                    json_cfg = get_config()
                    if key in json_cfg:
                        val = json_cfg[key]
                except:
                    pass
            
            # 如果都没有，使用默认值
            if val is None:
                val = default
            
            # 强化类型转换
            final_val = val
            if isinstance(val, str):
                if val.lower() == "true": final_val = True
                elif val.lower() == "false": final_val = False
            
            async with cls._lock:
                cls._cache[key] = final_val
            return final_val

    @classmethod
    async def set(cls, key: str, value: Any, description: str = None):
        # 1. 持久化到数据库 (保持 Infrastructure 模块兼容性)
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(SystemConfig).where(SystemConfig.key == key))
            config = result.scalars().first()
            
            str_val = str(value).lower() if isinstance(value, bool) else str(value)
            
            if config:
                config.value = str_val
                if description:
                    config.description = description
            else:
                config = SystemConfig(key=key, value=str_val, description=description)
                session.add(config)
            await session.commit()

        # 2. 同步到 config.json (符合 Lens 规范)
        try:
            from app.core.config_manager import get_config, save_config
            full_config = get_config()
            full_config[key] = value
            save_config(full_config)
        except Exception as e:
            print(f"Failed to sync {key} to config.json: {e}")
            
        async with cls._lock:
            cls._cache[key] = value

    @classmethod
    async def refresh_cache(cls):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(SystemConfig))
            configs = result.scalars().all()
            async with cls._lock:
                cls._cache.clear()
                for c in configs:
                    val = c.value
                    if val == "true": val = True
                    elif val == "false": val = False
                    cls._cache[c.key] = val
