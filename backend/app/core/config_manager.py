import json
import os
from typing import Dict, Any

CONFIG_FILE = "data/config.json"

DEFAULT_CONFIG = {
    "name": "默认服务器",
    "url": "",
    "api_key": "",
    "user_id": "",
    "tmdb_api_key": "",
    "bangumi_api_token": "",
    "username": "",
    "password": "",
    "session_token": "",
    "dedupe_rules": {
        "priority_order": ["display_title", "video_codec", "video_range"],
        "values_weight": {
            "display_title": ["4k", "2160p", "1080p", "720p"],
            "video_codec": ["hevc", "h265", "h264", "av1"],
            "video_range": ["hdr", "dolbyvision", "sdr"]
        },
        "tie_breaker": "small_id"
    },
    "exclude_paths": [],
    "autotag_rules": [],
    "webhook": {
        "enabled": True,
        "secret_token": "lens_default_token",
        "automation_enabled": True,
        "delay_seconds": 10,
        "write_mode": "merge"
    },
    "proxy": {
        "enabled": False,
        "url": "",
        "exclude_emby": True
    },
    "docker_hosts": [],
    "docker_container_settings": {},
    "pgsql_hosts": [],
    "backup_tasks": [],
    "menu_settings": []
}

def get_config() -> Dict[str, Any]:
    """从 config.json 读取配置，强制执行深度类型检查，防止 null 值破坏前端"""
    full_config = DEFAULT_CONFIG.copy()
    
    if not os.path.exists(CONFIG_FILE):
        return full_config
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            if not raw_data or not isinstance(raw_data, dict):
                return full_config
            
            # 基础字段合并
            for key in full_config.keys():
                if key in raw_data:
                    val = raw_data[key]
                    
                    # 关键防御：如果默认值是字典，但原始数据是 null，则保留默认字典
                    if isinstance(full_config[key], dict):
                        if isinstance(val, dict):
                            # 进行二级合并
                            sub = full_config[key].copy()
                            sub.update(val)
                            full_config[key] = sub
                        else:
                            # 原始数据非法（如为 null），维持默认值
                            pass
                    elif isinstance(full_config[key], list):
                        if isinstance(val, list):
                            full_config[key] = val
                        else:
                            full_config[key] = []
                    else:
                        full_config[key] = val if val is not None else full_config[key]
                        
            return full_config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data: Dict[str, Any]):
    """将配置保存到 config.json，保存前确保没有非法 null"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)