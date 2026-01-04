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
    "autotag_rules": [
        {
            "name": "国漫标记",
            "tag": "国漫",
            "item_type": "series",
            "match_all_conditions": True,
            "conditions": {
                "countries": ["中国大陆"],
                "genres": ["动画"],
                "years_text": ""
            }
        }
    ],
    "webhook": {
        "enabled": True,
        "secret_token": "embylens_default_token",
        "automation_enabled": True,
        "delay_seconds": 10,
        "write_mode": "merge"
    }
}

def get_config() -> Dict[str, Any]:
    """从 config.json 读取配置，并合并默认值"""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 基础合并
            full_config = DEFAULT_CONFIG.copy()
            full_config.update(data)
            
            # 深度合并二级对象，防止缺失字段
            for key in ["dedupe_rules", "webhook"]:
                if key in data:
                    sub_config = DEFAULT_CONFIG[key].copy()
                    sub_config.update(data[key])
                    full_config[key] = sub_config
                
            return full_config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data: Dict[str, Any]):
    """将配置保存到 config.json"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)