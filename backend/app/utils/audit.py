import json
import asyncio
import os
from typing import List, Dict, Any
from app.utils.time import get_local_time

# 审计日志目录
AUDIT_LOG_DIR = "/app/data/logs/audit"
os.makedirs(AUDIT_LOG_DIR, exist_ok=True)

# 内存缓冲区
audit_buffer = []
MAX_BUFFER_SIZE = 200

async def mask_sensitive_data(data: Any) -> Any:
    """脱敏处理"""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if any(secret in k.lower() for secret in ["password", "token", "secret", "key", "auth"]):
                masked[k] = "******"
            else:
                masked[k] = await mask_sensitive_data(v)
        return masked
    elif isinstance(data, list):
        return [await mask_sensitive_data(item) for item in data]
    return data

async def add_audit_log(
    method: str,
    path: str,
    status_code: int,
    client_ip: str,
    process_time: float,
    query_params: str = None,
    payload: str = None
):
    """添加审计日志：内存缓存 + 物理文件持久化 (使用本地时间)"""
    now = get_local_time()
    log_entry = {
        "id": int(now.timestamp() * 1000),
        "method": method,
        "path": path,
        "status_code": status_code,
        "client_ip": client_ip,
        "process_time": process_time,
        "query_params": query_params,
        "payload": payload,
        "timestamp": now.isoformat()
    }
    
    audit_buffer.insert(0, log_entry)
    if len(audit_buffer) > MAX_BUFFER_SIZE:
        audit_buffer.pop()

    current_date = now.strftime("%Y-%m-%d")
    audit_file = os.path.join(AUDIT_LOG_DIR, f"audit-{current_date}.jsonl")
    try:
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Error writing audit log: {e}")