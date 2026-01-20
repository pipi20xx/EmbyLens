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
    is_superuser: bool = False

class DbCreateRequest(BaseModel):
    dbname: str
    owner: Optional[str] = None
