import json
import os
import time
from typing import List, Dict, Any, Optional

NAV_FILE = "data/navigation.json"

DEFAULT_NAV = {
    "categories": [
        {"id": 1, "name": "默认", "order": 0}
    ],
    "sites": []
}

def get_nav_data() -> Dict[str, Any]:
    if not os.path.exists(NAV_FILE):
        return DEFAULT_NAV.copy()
    try:
        with open(NAV_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 确保基本结构存在
            if "categories" not in data: data["categories"] = DEFAULT_NAV["categories"]
            if "sites" not in data: data["sites"] = []
            return data
    except Exception:
        return DEFAULT_NAV.copy()

def save_nav_data(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(NAV_FILE), exist_ok=True)
    with open(NAV_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 分类操作 ---
def list_categories():
    return get_nav_data()["categories"]

def add_category(name: str):
    data = get_nav_data()
    new_id = int(time.time() * 1000)
    data["categories"].append({"id": new_id, "name": name, "order": 0})
    save_nav_data(data)
    return new_id

def delete_category(cat_id: int):
    data = get_nav_data()
    data["categories"] = [c for c in data["categories"] if c["id"] != cat_id]
    # 同时清理该分类下的站点，或者将其归为“默认”
    for site in data["sites"]:
        if site.get("category_id") == cat_id:
            site["category_id"] = None
            site["category"] = "未分类"
    save_nav_data(data)

def reorder_categories(ordered_ids: List[int]):
    data = get_nav_data()
    cat_map = {c["id"]: c for c in data["categories"]}
    new_cats = []
    for idx, cid in enumerate(ordered_ids):
        if cid in cat_map:
            cat = cat_map[cid]
            cat["order"] = idx
            new_cats.append(cat)
    
    # 补全
    existing_ids = set(ordered_ids)
    for c in data["categories"]:
        if c["id"] not in existing_ids:
            new_cats.append(c)
            
    data["categories"] = new_cats
    save_nav_data(data)
    return True

# --- 站点操作 ---
def list_sites():
    data = get_nav_data()
    # 动态关联分类名称
    cat_map = {c["id"]: c["name"] for c in data["categories"]}
    for site in data["sites"]:
        site["category"] = cat_map.get(site.get("category_id"), "未分类")
    return data["sites"]

def add_site(site_data: Dict[str, Any]):
    data = get_nav_data()
    site_data["id"] = int(time.time() * 1000)
    data["sites"].append(site_data)
    save_nav_data(data)
    return site_data

def update_site(site_id: int, update_data: Dict[str, Any]):
    data = get_nav_data()
    for i, site in enumerate(data["sites"]):
        if site["id"] == site_id:
            data["sites"][i].update(update_data)
            break
    save_nav_data(data)
    return True

def delete_site(site_id: int):
    data = get_nav_data()
    data["sites"] = [s for s in data["sites"] if s["id"] != site_id]
    save_nav_data(data)

def reorder_sites(ordered_ids: List[int]):
    data = get_nav_data()
    # 创建一个 ID 到站点的映射
    site_map = {s["id"]: s for s in data["sites"]}
    new_sites = []
    for idx, sid in enumerate(ordered_ids):
        if sid in site_map:
            site = site_map[sid]
            site["order"] = idx
            new_sites.append(site)
    
    # 补全可能没在列表里的站点（安全兜底）
    existing_ids = set(ordered_ids)
    for s in data["sites"]:
        if s["id"] not in existing_ids:
            new_sites.append(s)
            
    data["sites"] = new_sites
    save_nav_data(data)
    return True
