from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ConfigUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class BatchConfigUpdate(BaseModel):
    configs: List[ConfigUpdate]

class AuditLogResponse(BaseModel):
    id: int
    timestamp: str
    method: str
    path: str
    status_code: int
    client_ip: str
    query_params: Optional[str]
    payload: Optional[str]
    process_time: float

class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogResponse]
