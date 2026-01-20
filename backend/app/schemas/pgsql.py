from pydantic import BaseModel, Field
from typing import List, Any, Optional, Dict

class PostgresConfig(BaseModel):
    host: str = Field(..., example="localhost")
    port: int = Field(5432, example=5432)
    username: str = Field(..., example="postgres")
    password: str = Field(..., example="password")
    database: str = Field("postgres", example="postgres")

class PostgresHost(PostgresConfig):
    id: str
    name: str

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    version: Optional[str] = None

class TableListResponse(BaseModel):
    tables: List[str]

class QueryParams(BaseModel):
    table_name: str
    page: int = 1
    page_size: int = 50

class ColumnDefinition(BaseModel):
    name: str
    type: str

class DataViewerResponse(BaseModel):
    columns: List[ColumnDefinition]
    rows: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int

class UserCreateRequest(BaseModel):
    username: str
    password: str
    can_login: bool = True
    is_superuser: bool = False
    can_create_db: bool = False
    can_create_role: bool = False
    inherit: bool = True
    replication: bool = False
    bypass_rls: bool = False
    connection_limit: int = -1

class UserUpdateRequest(BaseModel):
    password: Optional[str] = None
    can_login: Optional[bool] = None
    is_superuser: Optional[bool] = None
    can_create_db: Optional[bool] = None
    can_create_role: Optional[bool] = None
    inherit: Optional[bool] = None
    replication: Optional[bool] = None
    bypass_rls: Optional[bool] = None
    connection_limit: Optional[int] = None
    valid_until: Optional[str] = None

class DbCreateRequest(BaseModel):
    dbname: str
    owner: Optional[str] = None

class DbUpdateRequest(BaseModel):
    owner: Optional[str] = None
    description: Optional[str] = None

class DbInfo(BaseModel):
    name: str
    owner: str
    description: Optional[str] = None
