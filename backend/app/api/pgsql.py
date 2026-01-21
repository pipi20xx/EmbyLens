from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from app.schemas.pgsql import (
    PostgresConfig, PostgresHost, TestConnectionResponse, TableListResponse,
    QueryParams, DataViewerResponse, UserCreateRequest, DbCreateRequest,
    DbInfo, DbUpdateRequest, UserUpdateRequest, BackupInfo, BackupCreateRequest
)
from app.services.pgsql_service import PostgresService
from app.core.config_manager import get_config, save_config

router = APIRouter()

# --- 备份管理 ---

@router.get("/backups", response_model=List[BackupInfo])
async def list_backups():
    try:
        return await PostgresService.list_backups()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/backups/create")
async def create_backup(config: PostgresConfig, req: BackupCreateRequest):
    try:
        filename = await PostgresService.create_backup(config, req.dbname)
        return {"message": f"Backup created: {filename}", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/backups/restore/{filename}")
async def restore_backup(filename: str, config: PostgresConfig, dbname: str):
    try:
        await PostgresService.restore_backup(config, dbname, filename)
        return {"message": f"Database {dbname} restored from {filename}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/backups/{filename}")
async def delete_backup(filename: str):
    try:
        await PostgresService.delete_backup(filename)
        return {"message": f"Backup {filename} deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@router.put("/hosts/{host_id}", response_model=PostgresHost)
async def update_host(host_id: str, host: PostgresConfig, name: str):
    config = get_config()
    hosts = config.get("pgsql_hosts", [])
    for i, h in enumerate(hosts):
        if h["id"] == host_id:
            updated_host = PostgresHost(**host.model_dump(), id=host_id, name=name)
            hosts[i] = updated_host.model_dump()
            config["pgsql_hosts"] = hosts
            save_config(config)
            return updated_host
    raise HTTPException(status_code=404, detail="Host not found")

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

@router.post("/databases/create")
async def create_database(config: PostgresConfig, req: DbCreateRequest):
    try:
        await PostgresService.create_database(config, req.dbname, req.owner)
        return {"message": f"Database {req.dbname} created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/databases/{dbname}")
async def update_database(dbname: str, config: PostgresConfig, req: DbUpdateRequest):
    try:
        await PostgresService.update_database(config, dbname, req.owner, req.description)
        return {"message": f"Database {dbname} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/databases/{dbname}")
async def drop_database(dbname: str, config: PostgresConfig):
    try:
        await PostgresService.drop_database(config, dbname)
        return {"message": f"Database {dbname} dropped successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- 用户/角色操作 ---

@router.post("/users", response_model=List[dict])
async def get_users(config: PostgresConfig):
    try:
        return await PostgresService.get_users(config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@router.delete("/users/{username}")
async def drop_user(username: str, config: PostgresConfig):
    try:
        await PostgresService.drop_user(config, username)
        return {"message": f"User {username} dropped successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- 数据/表操作 ---

@router.post("/tables", response_model=TableListResponse)
async def get_tables(config: PostgresConfig):
    try:
        tables = await PostgresService.get_tables(config)
        return TableListResponse(tables=tables)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/data", response_model=DataViewerResponse)
async def get_table_data(config: PostgresConfig, params: QueryParams):
    try:
        columns, rows, total = await PostgresService.get_table_data(
            config, params.table_name, params.page, params.page_size
        )
        return DataViewerResponse(
            columns=columns,
            rows=rows,
            total=total,
            page=params.page,
            page_size=params.page_size
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
