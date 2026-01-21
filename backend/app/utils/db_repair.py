import logging
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine
from app.db.session import Base

logger = logging.getLogger(__name__)

async def repair_database_schema(engine: AsyncEngine):
    """
    自动检测并修复数据库 Schema 缺失的列。
    对比 SQLAlchemy 模型定义与数据库真实结构，自动执行 ALTER TABLE ADD COLUMN。
    """
    async with engine.connect() as conn:
        # 获取数据库当前结构 (同步执行 inspect)
        def get_inspector(connection):
            return inspect(connection)
        
        inspector = await conn.run_sync(get_inspector)
        
        # 遍历 Base 中注册的所有表模型
        for table_name, table in Base.metadata.tables.items():
            # 1. 检查表是否存在
            if not await conn.run_sync(lambda c: inspector.has_table(table_name)):
                continue # 表不存在由 create_all 处理，这里只处理“增量列修复”
            
            # 2. 获取数据库中真实的列名
            existing_columns = [
                col["name"] for col in await conn.run_sync(lambda c: inspector.get_columns(table_name))
            ]
            
            # 3. 对比模型定义的列
            for column in table.columns:
                if column.name not in existing_columns:
                    logger.warning(f"🔧 [DB Repair] 发现表 {table_name} 缺失列: {column.name}，正在尝试修复...")
                    
                    # 构造 ALTER TABLE 命令
                    # 获取列的类型字符串表示 (处理 SQLite 特性)
                    col_type = str(column.type.compile(engine.dialect))
                    
                    # 默认值处理
                    default_clause = ""
                    if column.default is not None:
                        # 简单处理标量默认值
                        if hasattr(column.default, 'arg') and not callable(column.default.arg):
                            val = column.default.arg
                            if isinstance(val, str): val = f"'{val}'"
                            default_clause = f" DEFAULT {val}"
                    
                    # 是否允许为空
                    nullable_clause = " NOT NULL" if not column.nullable and default_clause else ""

                    ddl = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}{default_clause}{nullable_clause}"
                    
                    try:
                        await conn.execute(text(ddl))
                        await conn.commit()
                        logger.info(f"✅ [DB Repair] 表 {table_name} 成功补齐列: {column.name}")
                    except Exception as e:
                        logger.error(f"❌ [DB Repair] 修复表 {table_name} 失败: {e}")

async def init_db_with_repair(engine: AsyncEngine):
    """
    带自愈功能的数据库初始化入口
    """
    # 1. 创建不存在的表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. 修复现有表缺失的列
    await repair_database_schema(engine)
