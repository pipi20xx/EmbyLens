from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from app.schemas.pgsql import (
    PostgresConfig, PostgresHost, TestConnectionResponse, TableListResponse,
    QueryParams, DataViewerResponse, UserCreateRequest, DbCreateRequest,
    DbInfo, DbUpdateRequest, UserUpdateRequest
)
from app.services.pgsql_service import PostgresService
from app.core.config_manager import get_config, save_config

router = APIRouter()

# --- 主机管理 (CRUD) ---

@router.get("/hosts", response_model=List[PostgresHost])
async def get_hosts():
    config = get_config()
    return config.get("pgsql_hosts", [])

@router.post("/hosts", response_model=PostgresHost)
async def add_host(host: PostgresConfig, name: str):
    config = get_config()
    hosts = config.get("pgsql_hosts", [])
    new_host = PostgresHost(**host.model_dump(), id=str(uuid.uuid4()), name=name)
    hosts.append(new_host.model_dump())
    config["pgsql_hosts"] = hosts
    save_config(config)
    return new_host

@router.delete("/hosts/{host_id}")
async def delete_host(host_id: str):
    config = get_config()
    hosts = config.get("pgsql_hosts", [])
    config["pgsql_hosts"] = [h for h in hosts if h["id"] != host_id]
    save_config(config)
    return {"message": "Host deleted"}

# --- 数据库操作 ---

@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(config: PostgresConfig):
    success, message, version = await PostgresService.test_connection(config)
    return TestConnectionResponse(success=success, message=message, version=version)

@router.post("/databases", response_model=List[DbInfo])
async def get_databases(config: PostgresConfig):
    try:
        return await PostgresService.get_databases(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/databases/{dbname}")
async def update_database(dbname: str, config: PostgresConfig, req: DbUpdateRequest):
    try:
        await PostgresService.update_database(config, dbname, req.owner, req.description)
        return {"message": f"Database {dbname} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/users", response_model=List[dict])
async def get_users(config: PostgresConfig):
    try:
        return await PostgresService.get_users(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/users/{username}")
async def update_user(username: str, config: PostgresConfig, req: UserUpdateRequest):
    try:
        await PostgresService.update_user(
            config, username, req.password, req.can_login, req.is_superuser, 
            req.can_create_db, req.can_create_role, req.inherit,
            req.replication, req.bypass_rls, req.connection_limit, req.valid_until
        )
        return {"message": f"User {username} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ... (中间代码)

@router.post("/users/create")
async def create_user(config: PostgresConfig, req: UserCreateRequest):
    try:
        await PostgresService.create_user(
            config, req.username, req.password, req.can_login, req.is_superuser,
            req.can_create_db, req.can_create_role, req.inherit,
            req.replication, req.bypass_rls, req.connection_limit
        )
        return {"message": f"User {req.username} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{username}")
async def drop_user(username: str, config: PostgresConfig):
    try:
        await PostgresService.drop_user(config, username)
        return {"message": f"User {username} dropped successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/databases/create")
async def create_database(config: PostgresConfig, req: DbCreateRequest):
    try:
        await PostgresService.create_database(config, req.dbname, req.owner)
        return {"message": f"Database {req.dbname} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/databases/{dbname}")
async def drop_database(dbname: str, config: PostgresConfig):
    try:
        await PostgresService.drop_database(config, dbname)
        return {"message": f"Database {dbname} dropped successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))