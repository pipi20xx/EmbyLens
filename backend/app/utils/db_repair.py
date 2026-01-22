import logging
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine
from app.db.session import Base

logger = logging.getLogger(__name__)

async def repair_database_schema(engine: AsyncEngine):
    """
    自动检测并修复数据库 Schema。
    1. 检测主键冲突：针对 media_items，如果 server_id 不是主键（旧架构），强制重建表。
    2. 补全缺失列：执行 ALTER TABLE ADD COLUMN。
    """
    async with engine.connect() as conn:
        def get_inspector(connection):
            return inspect(connection)
        
        inspector = await conn.run_sync(get_inspector)
        
        # --- 针对 media_items 的破坏性主键迁移 ---
        if await conn.run_sync(lambda c: inspector.has_table("media_items")):
            pk_info = await conn.run_sync(lambda c: inspector.get_pk_constraint("media_items"))
            pk_cols = pk_info.get("constrained_columns", [])
            # 如果主键只有 id (旧架构)，则需要重建
            if "server_id" not in pk_cols:
                logger.warning("⚠️ [DB Repair] 检测到 media_items 仍在使用旧的单主键架构，正在执行物理重建以支持多服务器...")
                try:
                    await conn.execute(text("DROP TABLE media_items"))
                    await conn.commit()
                    # 重新创建表将由 init_db_with_repair 的 create_all 完成
                    logger.info("✅ [DB Repair] media_items 表已清理，准备重建复合主键架构")
                except Exception as e:
                    logger.error(f"❌ [DB Repair] 清理旧表失败: {e}")

        # 重新加载 inspector (如果刚才删了表)
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
    # 1. 先进行破坏性修复检测 (针对主键更改等 create_all 无法处理的情况)
    await repair_database_schema(engine)

    # 2. 创建所有不存在的表 (包含被 repair 删掉后需要重建的表)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
