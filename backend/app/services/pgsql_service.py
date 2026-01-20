import json
from datetime import datetime, date, time
from uuid import UUID
from typing import List, Dict, Any, Tuple, Optional
import psycopg
from psycopg import sql
from app.utils.logger import logger
from app.schemas.pgsql import PostgresConfig, ColumnDefinition

class PostgresService:
    _instances: Dict[str, Any] = {}

    @staticmethod
    def _get_cache_key(config: PostgresConfig) -> str:
        return f"{config.host}:{config.port}:{config.username}:{config.database}"

    @classmethod
    async def get_connection(cls, config: PostgresConfig):
        """获取或创建连接 (这里简化处理，直接返回新连接或维护一个简单的单例)"""
        # 注意：在生产环境中通常使用 Connection Pool (psycopg.AsyncConnectionPool)
        # 这里为了演示核心逻辑，使用常规连接。
        conn_str = f"host={config.host} port={config.port} user={config.username} password={config.password} dbname={config.database} connect_timeout=5"
        return await psycopg.AsyncConnection.connect(conn_str, autocommit=True)

    @classmethod
    async def test_connection(cls, config: PostgresConfig) -> Tuple[bool, str, Optional[str]]:
        try:
            async with await cls.get_connection(config) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT version();")
                    version = await cur.fetchone()
                    return True, "连接成功", version[0] if version else None
        except Exception as e:
            logger.error(f"PG Connection Test Failed: {str(e)}")
            return False, f"连接失败: {str(e)}", None

    @staticmethod
    def json_serializer(obj):
        """处理 Postgres 特殊类型到 JSON 的转换"""
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return str(obj)

    @classmethod
    async def get_databases(cls, config: PostgresConfig) -> List[str]:
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
                rows = await cur.fetchall()
                return [row[0] for row in rows]

    @classmethod
    async def get_users(cls, config: PostgresConfig) -> List[Dict[str, Any]]:
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT usename, usesuper, usecreatedb 
                    FROM pg_user;
                """)
                rows = await cur.fetchall()
                return [
                    {"username": r[0], "is_superuser": r[1], "can_create_db": r[2]} 
                    for r in rows
                ]

    @classmethod
    async def get_tables(cls, config: PostgresConfig) -> List[str]:
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                rows = await cur.fetchall()
                return [row[0] for row in rows]

    @classmethod
    async def get_table_data(cls, config: PostgresConfig, table_name: str, page: int, page_size: int):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                # 1. 获取列定义 (防止 SQL 注入：不要直接拼接表名到查询中，除非通过 sql.Identifier)
                # information_schema 是安全的
                await cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """, (table_name,))
                col_rows = await cur.fetchall()
                columns = [ColumnDefinition(name=r[0], type=r[1]) for r in col_rows]

                # 2. 获取总数
                # 使用 psycopg.sql 安全构建查询
                count_query = sql.SQL("SELECT COUNT(*) FROM {table}").format(
                    table=sql.Identifier(table_name)
                )
                await cur.execute(count_query)
                total = (await cur.fetchone())[0]

                # 3. 获取分页数据
                offset = (page - 1) * page_size
                data_query = sql.SQL("SELECT * FROM {table} LIMIT {limit} OFFSET {offset}").format(
                    table=sql.Identifier(table_name),
                    limit=sql.Literal(page_size),
                    offset=sql.Literal(offset)
                )
                await cur.execute(data_query)
                rows = await cur.fetchall()

                # 转换为字典列表
                formatted_rows = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        val = row[i]
                        # 序列化特殊类型
                        if isinstance(val, (datetime, date, time, UUID, dict, list)):
                            row_dict[col.name] = cls.json_serializer(val)
                        else:
                            row_dict[col.name] = val
                    formatted_rows.append(row_dict)

                return columns, formatted_rows, total

    @classmethod
    async def create_user(cls, config: PostgresConfig, username: str, password: str, is_superuser: bool):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                role_type = "SUPERUSER" if is_superuser else "NOSUPERUSER"
                query = sql.SQL("CREATE USER {user} WITH PASSWORD {password} {role}").format(
                    user=sql.Identifier(username),
                    password=sql.Literal(password),
                    role=sql.Placeholder()
                )
                # 注意：CREATE USER 不支持 Placeholder 里的关键字，需要特殊处理
                # 这里简单拼接受限关键词
                raw_sql = f"CREATE USER {sql.Identifier(username).as_string(conn)} WITH PASSWORD {sql.Literal(password).as_string(conn)} {role_type}"
                await cur.execute(raw_sql)

    @classmethod
    async def drop_user(cls, config: PostgresConfig, username: str):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                query = sql.SQL("DROP USER {user}").format(user=sql.Identifier(username))
                await cur.execute(query)

    @classmethod
    async def create_database(cls, config: PostgresConfig, dbname: str, owner: str = None):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                if owner:
                    query = sql.SQL("CREATE DATABASE {db} OWNER {owner}").format(
                        db=sql.Identifier(dbname),
                        owner=sql.Identifier(owner)
                    )
                else:
                    query = sql.SQL("CREATE DATABASE {db}").format(db=sql.Identifier(dbname))
                await cur.execute(query)

    @classmethod
    async def drop_database(cls, config: PostgresConfig, dbname: str):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                # 核心逻辑：强制终止所有连接到该数据库的会话，否则无法删除
                await cur.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid();
                """, (dbname,))
                
                query = sql.SQL("DROP DATABASE {db}").format(db=sql.Identifier(dbname))
                await cur.execute(query)
