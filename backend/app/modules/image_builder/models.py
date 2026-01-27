from sqlalchemy import Boolean, Column, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from app.db.session import Base

class BuildProject(Base):
    __tablename__ = "build_projects"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    host_id = Column(String, nullable=True) # ID of the docker host from config
    build_context = Column(String, nullable=False)
    dockerfile_path = Column(String, nullable=False)
    local_image_name = Column(String, nullable=False)
    repo_image_name = Column(String, nullable=False)
    no_cache = Column(Boolean, default=False, nullable=False)
    auto_cleanup = Column(Boolean, default=True, nullable=False)
    platforms = Column(String, default="linux/amd64", nullable=False)
    registry_id = Column(String, ForeignKey("build_registries.id"), nullable=True)
    proxy_id = Column(String, ForeignKey("build_proxies.id"), nullable=True)
    backup_ignore_patterns = Column(String, nullable=True, default="")

class BuildRegistry(Base):
    __tablename__ = "build_registries"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    url = Column(String, nullable=False)
    is_https = Column(Boolean, default=True, nullable=False)
    credential_id = Column(String, ForeignKey("build_credentials.id"), nullable=True)

class BuildCredential(Base):
    __tablename__ = "build_credentials"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    encrypted_password = Column(String, nullable=False)

class BuildProxy(Base):
    __tablename__ = "build_proxies"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    url = Column(String, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)

class BuildTaskLog(Base):
    __tablename__ = "build_task_logs"
    id = Column(String, primary_key=True, index=True) # task_id
    project_id = Column(String, ForeignKey("build_projects.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String, nullable=False)
    status = Column(String, default="PENDING", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
