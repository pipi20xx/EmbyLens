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

def reorder_bookmarks(ordered_ids: List[str], parent_id: Optional[str] = None):
    data = get_data()
    bm_map = {str(bm["id"]): bm for bm in data.get("bookmarks", [])}
    for idx, bmid in enumerate(ordered_ids):
        if bmid in bm_map:
            bm_map[bmid]["order"] = idx
            if parent_id is not None:
                bm_map[bmid]["parent_id"] = parent_id
    save_data(data)
    return True

def clear_bookmarks():
    save_data({"bookmarks": []})
    return True

def export_bookmarks_to_html() -> str:
    tree = list_bookmarks(as_tree=True)
    lines = [
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        '<TITLE>Bookmarks</TITLE><H1>Bookmarks</H1><DL><p>'
    ]
    def traverse(items, level):
        indent = '    ' * level
        for it in items:
            if it['type'] == 'folder':
                lines.append(f'{indent}<DT><H3>{it["title"]}</H3><DL><p>')
                if it.get('children'): traverse(it['children'], level + 1)
                lines.append(f'{indent}</DL><p>')
            else:
                icon = f' ICON="{it["icon"]}"' if it.get('icon') else ''
                lines.append(f'{indent}<DT><A HREF="{it["url"]}"{icon}>{it["title"]}</A>')
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
