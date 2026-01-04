import json
import os
from typing import Dict, Any

CONFIG_FILE = "data/config.json"

def get_config() -> Dict[str, Any]:
    """从 config.json 读取配置"""
    if not os.path.exists(CONFIG_FILE):
        return {
            "name": "默认服务器",
            "url": "",
            "api_key": "",
            "user_id": "",
            "tmdb_api_key": "",
            "username": "",
            "password": "",
            "session_token": ""
        }
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(config_data: Dict[str, Any]):
    """将配置保存到 config.json"""
    # 确保目录存在
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
