# 此文件已弃用，配置已迁移至 config.json
# 保留空文件或基础结构以防止导入错误
from sqlalchemy import Column, Integer, String, Boolean
from app.db.session import Base
import time

# 暂时保留类定义但不再使用，避免大规模重构导入逻辑
class EmbyServer(Base):
    __tablename__ = "emby_servers"
    id = Column(Integer, primary_key=True, index=True)
    # 移除所有字段，不再通过数据库访问
