import json
import os
import time
import copy
from typing import List, Dict, Any, Optional

NAV_FILE = "data/navigation.json"

DEFAULT_NAV = {
    "categories": [
        {"id": 1, "name": "默认", "order": 0}
    ],
    "sites": [],
    "settings": {
        "background_url": "",
        "background_opacity": 0.7,
        "background_blur": 0,
        "background_size": "cover",
        "background_color": "#1e1e22",
        "card_background": "rgba(255, 255, 255, 0.12)",
        "card_blur": 16,
        "card_border_color": "rgba(255, 255, 255, 0.15)",
        "card_style": "glass",
        "text_color": "#ffffff",
        "text_description_color": "rgba(255, 255, 255, 0.7)",
        "category_title_color": "#ffffff",
        "content_max_width": 90,
        "page_title": "站点导航",
        "page_subtitle": "个性化您的导航面板"
    }
}

def normalize_nav_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    标准化导航数据：确保结构完整且兼容新旧版本
    """
    if not isinstance(data, dict):
        return copy.deepcopy(DEFAULT_NAV)
        
    full_data = copy.deepcopy(DEFAULT_NAV)
    
    # Categories: 如果存在且是列表则采用，否则保持默认
    if "categories" in data and isinstance(data["categories"], list):
        full_data["categories"] = data["categories"]
        
    # Sites: 同上
    if "sites" in data and isinstance(data["sites"], list):
        full_data["sites"] = data["sites"]
        
    # Settings: 深度合并
    if "settings" in data and isinstance(data["settings"], dict):
        user_settings = data["settings"]
        # 以默认设置为底板
        merged_settings = full_data["settings"]
        
        # 覆盖用户设置
        merged_settings.update(user_settings)
        
        # 确保所有默认键都存在（防御 update 中可能存在的 null 值覆盖默认值的情况，虽不常见）
        defaults = DEFAULT_NAV["settings"]
        for k, v in defaults.items():
            if merged_settings.get(k) is None and v is not None:
                 merged_settings[k] = v
                 
        full_data["settings"] = merged_settings

    return full_data

def get_nav_data() -> Dict[str, Any]:
    if not os.path.exists(NAV_FILE):
        return copy.deepcopy(DEFAULT_NAV)
    try:
        with open(NAV_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return normalize_nav_data(data)
    except Exception:
        return copy.deepcopy(DEFAULT_NAV)

# ... (中间函数保持不变)

def update_settings(new_settings: Dict[str, Any]):
    data = get_nav_data()
    data["settings"].update(new_settings)
    save_nav_data(data)
    return data["settings"]

def save_nav_data(data: Dict[str, Any]):
    from app.utils.config_backup import auto_backup_file
    
    # 自动备份旧版本
    auto_backup_file(NAV_FILE)

    os.makedirs(os.path.dirname(NAV_FILE), exist_ok=True)
    with open(NAV_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 分类操作 ---
def list_categories():
    return get_nav_data()["categories"]

def add_category(name: str, icon: Optional[str] = None, order: Optional[int] = None):
    data = get_nav_data()
    new_id = int(time.time() * 1000)
    
    if order is None:
        max_order = -1
        for c in data.get("categories", []):
            max_order = max(max_order, c.get("order", 0))
        order = max_order + 1

    new_cat = {
        "id": new_id, 
        "name": name, 
        "icon": icon,
        "order": order
    }
    data["categories"].append(new_cat)
    save_nav_data(data)
    return new_cat

def update_category(cat_id: int, name: str, icon: Optional[str] = None, order: Optional[int] = None):
    data = get_nav_data()
    # 1. 更新分类表中的名称、图标和排序
    for cat in data["categories"]:
        if str(cat["id"]) == str(cat_id):
            cat["name"] = name
            if icon is not None:
                cat["icon"] = icon
            if order is not None:
                cat["order"] = order
            break
    
    # 2. 联动更新：更新所有属于该分类的站点的冗余名称字段
    for site in data.get("sites", []):
        if str(site.get("category_id")) == str(cat_id):
            site["category"] = name
            
    save_nav_data(data)
    return True

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
    
    # 自动设置排序：获取当前所有站点的最大 order 并 + 1
    # 如果传入的 order 是 None，或者 order 是 0 且该分类下已有站点，则自动递增
    if site_data.get("order") is None or site_data.get("order") == 0:
        max_order = -1
        has_sites = False
        for s in data.get("sites", []):
            if s.get("category_id") == site_data.get("category_id"):
                max_order = max(max_order, s.get("order", 0))
                has_sites = True
        
        # 只有在确实需要递增的情况下（已有站点且传入为0/None）才重写
        if site_data.get("order") is None or has_sites:
            site_data["order"] = max_order + 1
        
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

def cleanup_orphaned_icons():
    """清理没有被任何站点或分类引用的图标文件"""
    data = get_nav_data()
    # 1. 收集所有正在使用的图标文件名
    used_icons = set()
    
    # 检查站点图标
    for site in data.get("sites", []):
        icon_path = site.get("icon")
        if icon_path and icon_path.startswith("/nav_icons/"):
            used_icons.add(os.path.basename(icon_path))
            
    # 检查分类图标 (新增逻辑)
    for cat in data.get("categories", []):
        cat_icon = cat.get("icon")
        if cat_icon and cat_icon.startswith("/nav_icons/"):
            used_icons.add(os.path.basename(cat_icon))
    
    # 2. 扫描物理目录
    icon_dir = "/app/data/nav_icons"
    if not os.path.exists(icon_dir):
        return
    
    cleaned_count = 0
    for filename in os.listdir(icon_dir):
        # 如果文件不在引用名单中，则删除
        if filename not in used_icons:
            try:
                os.remove(os.path.join(icon_dir, filename))
                cleaned_count += 1
            except Exception:
                pass
    
    if cleaned_count > 0:
        print(f"[Cleanup] Removed {cleaned_count} orphaned icons.")
    return cleaned_count

def cleanup_orphaned_backgrounds():
    """清理没有被使用的自定义背景文件"""
    data = get_nav_data()
    # 1. 收集正在使用的背景
    used_bgs = set()
    bg_url = data.get("settings", {}).get("background_url")
    if bg_url and bg_url.startswith("/nav_backgrounds/"):
        used_bgs.add(os.path.basename(bg_url))
        
    # 2. 扫描物理目录
    bg_dir = "/app/data/nav_backgrounds"
    if not os.path.exists(bg_dir):
        return 0
        
    cleaned_count = 0
    for filename in os.listdir(bg_dir):
        if filename not in used_bgs:
            try:
                os.remove(os.path.join(bg_dir, filename))
                cleaned_count += 1
            except Exception:
                pass
    
    if cleaned_count > 0:
        print(f"[Cleanup] Removed {cleaned_count} orphaned backgrounds.")
    return cleaned_count
