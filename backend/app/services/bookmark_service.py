import json
import os
import time
import copy
import re
from typing import List, Dict, Any, Optional

BOOKMARK_FILE = "data/bookmarks.json"

DEFAULT_DATA = {
    "bookmarks": []
}

def get_data() -> Dict[str, Any]:
    if not os.path.exists(BOOKMARK_FILE):
        return copy.deepcopy(DEFAULT_DATA)
    try:
        with open(BOOKMARK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else copy.deepcopy(DEFAULT_DATA)
    except:
        return copy.deepcopy(DEFAULT_DATA)

def save_data(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(BOOKMARK_FILE), exist_ok=True)
    with open(BOOKMARK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def list_bookmarks(as_tree: bool = False):
    data = get_data()
    bookmarks = data.get("bookmarks", [])
    if not as_tree:
        return bookmarks
    
    item_map = {str(item["id"]): {**item, "children": []} for item in bookmarks}
    tree = []
    sorted_items = sorted(item_map.values(), key=lambda x: x.get("order", 0))
    
    for item in sorted_items:
        p_id = item.get("parent_id")
        if p_id and str(p_id) in item_map:
            item_map[str(p_id)]["children"].append(item)
        else:
            tree.append(item)
    return tree

def add_bookmark(bookmark_data: Dict[str, Any]):
    data = get_data()
    if "id" not in bookmark_data:
        bookmark_data["id"] = f"bm_{int(time.time() * 1000)}"
    data.setdefault("bookmarks", []).append(bookmark_data)
    save_data(data)
    return bookmark_data

def update_bookmark(bm_id: str, update_data: Dict[str, Any]):
    data = get_data()
    found = False
    for i, bm in enumerate(data.get("bookmarks", [])):
        if str(bm["id"]) == str(bm_id):
            data["bookmarks"][i].update(update_data)
            found = True
            break
    if found:
        save_data(data)
    return found

def delete_bookmark(bm_id: str):
    data = get_data()
    ids_to_delete = {str(bm_id)}
    while True:
        added = False
        for bm in data.get("bookmarks", []):
            bid, pid = str(bm["id"]), str(bm.get("parent_id"))
            if pid in ids_to_delete and bid not in ids_to_delete:
                ids_to_delete.add(bid)
                added = True
        if not added: break
    
    original_len = len(data["bookmarks"])
    data["bookmarks"] = [bm for bm in data["bookmarks"] if str(bm["id"]) not in ids_to_delete]
    if len(data["bookmarks"]) != original_len:
        save_data(data)
        return True
    return False

def reorder_bookmarks(ordered_ids: List[str], parent_id: Any = "KEEP_EXISTING"):
    """
    重新排序。如果 parent_id 传入具体值（包括 None），则更新这些项的父级。
    """
    data = get_data()
    # 创建一个快速索引
    bm_lookup = {str(bm["id"]): i for i, bm in enumerate(data["bookmarks"])}
    
    for idx, bmid in enumerate(ordered_ids):
        if bmid in bm_lookup:
            target_idx = bm_lookup[bmid]
            data["bookmarks"][target_idx]["order"] = idx
            if parent_id != "KEEP_EXISTING":
                data["bookmarks"][target_idx]["parent_id"] = parent_id
                
    save_data(data)
    return True

def clear_bookmarks():
    save_data({"bookmarks": []})
    return True

def export_bookmarks_to_html() -> str:
    tree = list_bookmarks(as_tree=True)
    lines = [
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
        '<!-- This is an automatically generated file. -->',
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        '<TITLE>Bookmarks</TITLE>',
        '<H1>Bookmarks</H1>',
        '<DL><p>'
    ]
    def traverse(items, level):
        indent = '    ' * level
        for it in items:
            if it['type'] == 'folder':
                lines.append(f'{indent}<DT><H3>{it["title"]}</H3>')
                lines.append(f'{indent}<DL><p>')
                if it.get('children'): 
                    traverse(it['children'], level + 1)
                lines.append(f'{indent}</DL><p>')
            else:
                icon_attr = f' ICON="{it["icon"]}"' if it.get('icon') else ''
                lines.append(f'{indent}<DT><A HREF="{it["url"]}"{icon_attr}>{it["title"]}</A>')
    
    if tree:
        traverse(tree, 1)
        
    lines.append('</DL><p>')
    return '\n'.join(lines)

def import_from_html(html_content: str):
    data = get_data()
    data.setdefault("bookmarks", [])
    existing_urls = {bm.get("url") for bm in data["bookmarks"] if bm.get("type") == "file" and bm.get("url")}
    parent_stack, imported_count = [None], 0
    now_ms = int(time.time() * 1000)
    token_pattern = re.compile(r'<(H3|A|DL|/DL)([^>]*)>(.*?)(?=<|$)', re.I | re.S)
    last_folder_id = None
    for match in token_pattern.finditer(html_content):
        tag, attrs, inner = match.group(1).upper(), match.group(2), match.group(3)
        if tag == 'H3':
            title = re.sub(r'<[^>]+>', '', inner).split('</H3>')[0].strip()
            folder_id = f"bm_fld_{now_ms}_{imported_count}"
            data["bookmarks"].append({"id": folder_id, "type": "folder", "title": title or "文件夹", "parent_id": parent_stack[-1], "order": len(data["bookmarks"])})
            last_folder_id = folder_id
            imported_count += 1
        elif tag == 'DL':
            if last_folder_id: parent_stack.append(last_folder_id); last_folder_id = None
        elif tag == '/DL':
            if len(parent_stack) > 1: parent_stack.pop()
        elif tag == 'A':
            href_m = re.search(r'HREF=["\\]?([^"\\\'>\s]+)', attrs, re.I)
            if href_m:
                url = href_m.group(1)
                if url not in existing_urls:
                    title = re.sub(r'<[^>]+>', '', inner).split('</A>')[0].strip()
                    icon_m = re.search(r'ICON=["\\]?([^"\\\'>\s]+)', attrs, re.I)
                    data["bookmarks"].append({"id": f"bm_lnk_{now_ms}_{imported_count}", "type": "file", "title": title or url, "url": url, "icon": icon_m.group(1) if icon_m else None, "parent_id": parent_stack[-1], "order": len(data["bookmarks"])})
                    imported_count += 1
    if imported_count > 0: save_data(data)
    return imported_count

def find_duplicates() -> List[Dict[str, Any]]:
    """
    查找重复书签。返回重复组的列表。
    """
    data = get_data()
    bookmarks = data.get("bookmarks", [])
    
    url_map = {}
    # Flatten and group
    def traverse(items):
        for item in items:
            if item.get("type") == "file" and item.get("url"):
                u = item["url"].strip()
                if u not in url_map: url_map[u] = []
                url_map[u].append(item)
            # Flatten search handles parent_id logic in list_bookmarks generally, 
            # but raw data is flat list.
            # wait, get_data returns flat list. list_bookmarks(as_tree=True) returns tree.
            # checks raw list structure:
            # "bookmarks": [ {id, parent_id, ...} ]
            # So simple iteration is enough.
    
    # get_data returns the raw dict. bookmarks is a list.
    for item in bookmarks:
        if item.get("type") == "file" and item.get("url"):
            u = item["url"].strip()
            if u:
                if u not in url_map: url_map[u] = []
                url_map[u].append(item)

    duplicates = []
    for u, items in url_map.items():
        if len(items) > 1:
            duplicates.append({
                "url": u,
                "count": len(items),
                "items": items
            })
    return duplicates

import aiohttp
import asyncio

async def check_batch_health(urls: List[str]) -> Dict[str, int]:
    """
    并发检测一批 URL 的存活状态。
    返回 {url: status_code} (0 表示连接失败)
    """
    results = {}
    
    async def check_one(session, url):
        try:
            async with session.head(url, timeout=10, allow_redirects=True, ssl=False) as response:
                return url, response.status
        except:
            # Try GET if HEAD fails (some servers deny HEAD)
            try:
                async with session.get(url, timeout=10, allow_redirects=True, ssl=False) as response:
                    return url, response.status
            except:
                return url, 0

    async with aiohttp.ClientSession() as session:
        tasks = [check_one(session, u) for u in urls]
        res_list = await asyncio.gather(*tasks)
        for u, status in res_list:
            results[u] = status
            
    return results
