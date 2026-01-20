import json
import os
import subprocess
import asyncio
from datetime import datetime, date, time
from uuid import UUID
from typing import List, Dict, Any, Tuple, Optional
import psycopg
from psycopg import sql
from app.utils.logger import logger
from app.schemas.pgsql import PostgresConfig, ColumnDefinition, BackupInfo

class PostgresService:
    _instances: Dict[str, Any] = {}

    @staticmethod
    def _get_backup_dir() -> str:
        backup_dir = os.path.join("data", "backups", "pg")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @classmethod
    async def list_backups(cls) -> List[BackupInfo]:
        backup_dir = cls._get_backup_dir()
        backups = []
        for f in os.listdir(backup_dir):
            if f.endswith(".bak") or f.endswith(".sql"):
                path = os.path.join(backup_dir, f)
                stats = os.stat(path)
                # Try to extract db_name from filename: dbname_timestamp.bak
                parts = f.rsplit("_", 1)
                db_name = parts[0] if len(parts) > 1 else "unknown"
                backups.append(BackupInfo(
                    filename=f,
                    size=stats.st_size,
                    created_at=datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    db_name=db_name
                ))
        return sorted(backups, key=lambda x: x.created_at, reverse=True)

    @classmethod
    async def create_backup(cls, config: PostgresConfig, dbname: str):
        backup_dir = cls._get_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{dbname}_{timestamp}.bak"
        file_path = os.path.join(backup_dir, filename)

        env = os.environ.copy()
        env["PGPASSWORD"] = config.password

        cmd = [
            "pg_dump",
            "-h", config.host,
            "-p", str(config.port),
            "-U", config.username,
            "-F", "c",  # Custom format
            "-b",       # Include blobs
            "-v",       # Verbose
            "-f", file_path,
            dbname
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise Exception(f"Backup failed: {stderr.decode()}")

        return filename

    @classmethod
    async def restore_backup(cls, config: PostgresConfig, dbname: str, filename: str):
        backup_dir = cls._get_backup_dir()
        file_path = os.path.join(backup_dir, filename)
        
        if not os.path.exists(file_path):
            raise Exception("Backup file not found")

        env = os.environ.copy()
        env["PGPASSWORD"] = config.password

        # First terminate connections to the DB
        await cls.drop_database(config, dbname)
        await cls.create_database(config, dbname)

        cmd = [
            "pg_restore",
            "-h", config.host,
            "-p", str(config.port),
            "-U", config.username,
            "-d", dbname,
            "-v",
            file_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        # pg_restore often returns 0 even with warnings, but that's usually OK
        if process.returncode not in [0, 1]:
            raise Exception(f"Restore failed: {stderr.decode()}")

        return True

    @classmethod
    async def delete_backup(cls, filename: str):
        backup_dir = cls._get_backup_dir()
        file_path = os.path.join(backup_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    @staticmethod
    def _get_cache_key(config: PostgresConfig) -> str:
        return f"{config.host}:{config.port}:{config.username}:{config.database}"

    @classmethod
    async def get_connection(cls, config: PostgresConfig):
        """获取或创建连接 (这里简化处理，直接返回新连接或维护一个简单的单例)"""
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
        if isinstance(obj, (dict, list)):
            return obj
        return str(obj)

    @classmethod
    async def get_databases(cls, config: PostgresConfig) -> List[Dict[str, Any]]:
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT 
                        d.datname as name,
                        pg_catalog.pg_get_userbyid(d.datdba) as owner,
                        pg_catalog.shobj_description(d.oid, 'pg_database') as description
                    FROM pg_catalog.pg_database d
                    WHERE d.datistemplate = false
                    ORDER BY d.datname ASC;
                """)
                rows = await cur.fetchall()
                return [
                    {"name": r[0], "owner": r[1], "description": r[2]} 
                    for r in rows
                ]

    @classmethod
    async def update_database(cls, config: PostgresConfig, dbname: str, owner: str = None, description: str = None):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                if owner:
                    query = sql.SQL("ALTER DATABASE {db} OWNER TO {owner}").format(
                        db=sql.Identifier(dbname),
                        owner=sql.Identifier(owner)
                    )
                    await cur.execute(query)
                if description is not None:
                    query = sql.SQL("COMMENT ON DATABASE {db} IS {comment}").format(
                        db=sql.Identifier(dbname),
                        comment=sql.Literal(description)
                    )
                    await cur.execute(query)

    @classmethod
    async def get_users(cls, config: PostgresConfig) -> List[Dict[str, Any]]:
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT 
                        rolname, rolsuper, rolcreatedb, rolcreaterole, 
                        rolcanlogin, rolinherit, rolreplication, 
                        rolconnlimit, rolbypassrls, rolvaliduntil 
                    FROM pg_roles
                    WHERE rolname NOT LIKE 'pg_%'
                    ORDER BY rolname ASC;
                """)
                rows = await cur.fetchall()
                return [
                    {
                        "username": r[0], 
                        "is_superuser": r[1], 
                        "can_create_db": r[2],
                        "can_create_role": r[3],
                        "can_login": r[4],
                        "inherit": r[5],
                        "replication": r[6],
                        "connection_limit": r[7],
                        "bypass_rls": r[8],
                        "valid_until": cls.json_serializer(r[9]) if r[9] else None
                    } 
                    for r in rows
                ]

    @classmethod
    async def create_user(cls, config: PostgresConfig, username: str, password: str, 
                          can_login: bool = True, is_superuser: bool = False,
                          can_create_db: bool = False, can_create_role: bool = False,
                          inherit: bool = True, replication: bool = False, 
                          bypass_rls: bool = False, connection_limit: int = -1):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                parts = []
                parts.append("LOGIN" if can_login else "NOLOGIN")
                parts.append("SUPERUSER" if is_superuser else "NOSUPERUSER")
                parts.append("CREATEDB" if can_create_db else "NOCREATEDB")
                parts.append("CREATEROLE" if can_create_role else "NOCREATEROLE")
                parts.append("INHERIT" if inherit else "NOINHERIT")
                parts.append("REPLICATION" if replication else "NOREPLICATION")
                parts.append("BYPASSRLS" if bypass_rls else "NOBYPASSRLS")
                parts.append(f"CONNECTION LIMIT {connection_limit}")
                parts.append(f"PASSWORD {sql.Literal(password).as_string(conn)}")

                raw_sql = f"CREATE ROLE {sql.Identifier(username).as_string(conn)} {' '.join(parts)}"
                await cur.execute(raw_sql)

    @classmethod
    async def update_user(cls, config: PostgresConfig, username: str, 
                          password: str = None, can_login: bool = None,
                          is_superuser: bool = None, can_create_db: bool = None, 
                          can_create_role: bool = None, inherit: bool = None,
                          replication: bool = None, bypass_rls: bool = None,
                          connection_limit: int = None, valid_until: str = None):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                parts = []
                if password: parts.append(f"PASSWORD {sql.Literal(password).as_string(conn)}")
                if can_login is not None: parts.append("LOGIN" if can_login else "NOLOGIN")
                if is_superuser is not None: parts.append("SUPERUSER" if is_superuser else "NOSUPERUSER")
                if can_create_db is not None: parts.append("CREATEDB" if can_create_db else "NOCREATEDB")
                if can_create_role is not None: parts.append("CREATEROLE" if can_create_role else "NOCREATEROLE")
                if inherit is not None: parts.append("INHERIT" if inherit else "NOINHERIT")
                if replication is not None: parts.append("REPLICATION" if replication else "NOREPLICATION")
                if bypass_rls is not None: parts.append("BYPASSRLS" if bypass_rls else "NOBYPASSRLS")
                if connection_limit is not None: parts.append(f"CONNECTION LIMIT {connection_limit}")
                
                if valid_until:
                    val = "infinity" if valid_until == "infinity" else sql.Literal(valid_until).as_string(conn)
                    parts.append(f"VALID UNTIL {val}")

                if parts:
                    raw_sql = f"ALTER ROLE {sql.Identifier(username).as_string(conn)} {' '.join(parts)}"
                    await cur.execute(raw_sql)

    @classmethod
    async def get_tables(cls, config: PostgresConfig) -> List[str]:
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type IN ('BASE TABLE', 'VIEW', 'FOREIGN TABLE')
                    ORDER BY table_name;
                """)
                rows = await cur.fetchall()
                return [row[0] for row in rows]

    @classmethod
    async def get_table_data(cls, config: PostgresConfig, table_name: str, page: int, page_size: int):
        async with await cls.get_connection(config) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """, (table_name,))
                col_rows = await cur.fetchall()
                columns = [ColumnDefinition(name=r[0], type=r[1]) for r in col_rows]

                count_query = sql.SQL("SELECT COUNT(*) FROM {table}").format(
                    table=sql.Identifier(table_name)
                )
                await cur.execute(count_query)
                total = (await cur.fetchone())[0]

                offset = (page - 1) * page_size
                data_query = sql.SQL("SELECT * FROM {table} LIMIT {limit} OFFSET {offset}").format(
                    table=sql.Identifier(table_name),
                    limit=sql.Literal(page_size),
                    offset=sql.Literal(offset)
                )
                await cur.execute(data_query)
                rows = await cur.fetchall()

                formatted_rows = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        val = row[i]
                        if isinstance(val, (datetime, date, time, UUID, dict, list)):
                            row_dict[col.name] = cls.json_serializer(val)
                        else:
                            row_dict[col.name] = val
                    formatted_rows.append(row_dict)

                return columns, formatted_rows, total

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
                await cur.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid();
                """, (dbname,))
                query = sql.SQL("DROP DATABASE {db}").format(db=sql.Identifier(dbname))
                await cur.execute(query)
