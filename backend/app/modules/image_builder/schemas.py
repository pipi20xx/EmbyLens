from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- Credential Schemas ---
class CredentialBase(BaseModel):
    name: str
    username: str

class CredentialCreate(CredentialBase):
    password: str

class CredentialUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class Credential(CredentialBase):
    id: str
    class Config:
        from_attributes = True

# --- Proxy Schemas ---
class ProxyBase(BaseModel):
    name: str
    url: str
    username: Optional[str] = None
    password: Optional[str] = None

class ProxyCreate(ProxyBase):
    pass

class ProxyUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class Proxy(ProxyBase):
    id: str
    class Config:
        from_attributes = True

# --- Registry Schemas ---
class RegistryBase(BaseModel):
    name: str
    url: str
    is_https: bool = True
    credential_id: Optional[str] = None

class RegistryCreate(RegistryBase):
    pass

class RegistryUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    is_https: Optional[bool] = None
    credential_id: Optional[str] = None

class Registry(RegistryBase):
    id: str
    class Config:
        from_attributes = True

# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    host_id: Optional[str] = None
    build_context: str
    dockerfile_path: str
    local_image_name: str
    repo_image_name: str
    no_cache: bool = False
    auto_cleanup: bool = True
    platforms: str = "linux/amd64"
    registry_id: Optional[str] = None
    proxy_id: Optional[str] = None
    backup_ignore_patterns: Optional[str] = ""

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    build_context: Optional[str] = None
    dockerfile_path: Optional[str] = None
    local_image_name: Optional[str] = None
    repo_image_name: Optional[str] = None
    no_cache: Optional[bool] = None
    auto_cleanup: Optional[bool] = None
    platforms: Optional[str] = None
    registry_id: Optional[str] = None
    proxy_id: Optional[str] = None
    backup_ignore_patterns: Optional[str] = None

class Project(ProjectBase):
    id: str
    class Config:
        from_attributes = True

# --- Task Schemas ---
class TaskLogBase(BaseModel):
    project_id: str
    tag: str
    status: str = "PENDING"

class TaskLog(TaskLogBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class BuildRequest(BaseModel):
    tag: str = "latest"
