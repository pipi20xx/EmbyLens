import httpx
import json
from typing import List, Dict, Any, Optional, Literal
from app.utils.logger import logger

class AutotagEmbyHelper:
    def __init__(self, url: str, api_key: str, user_id: str = None):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.user_id = user_id
        self.headers = {
            "X-Emby-Token": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def _request(self, method: str, path: str, params: Dict = None, json_data: Dict = None):
        url = f"{self.url}/emby{path}"
        query_params = {"api_key": self.api_key}
        if params: query_params.update(params)
        logger.info(f"┃  ┣ 🚀 [AutoTag API] {method} {path}")
        async with httpx.AsyncClient(timeout=30.0, headers=self.headers) as client:
            try:
                resp = await client.request(method, url, params=query_params, json=json_data)
                return resp
            except Exception as e:
                logger.error(f"┃  ┃  ❌ 通讯异常: {str(e)}")
                return None

    def _extract_tags(self, item_data: Dict) -> List[str]:
        """统一 1:1 标签提取逻辑"""
        if "Tags" in item_data and item_data["Tags"]:
            return item_data["Tags"]
        if "TagItems" in item_data and item_data["TagItems"]:
            return [t.get('Name') for t in item_data["TagItems"] if t.get('Name')]
        return []

    async def get_all_items(self):
        # 必须带上 UserID 才能获取到 UserData（包含收藏状态）
        path = f"/Users/{self.user_id}/Items" if self.user_id else "/Items"
        params = {
            "IncludeItemTypes": "Movie,Series", 
            "Recursive": "true", 
            "Fields": "ProviderIds,Tags,TagItems,UserData"
        }
        resp = await self._request("GET", path, params=params)
        return resp.json().get("Items", []) if resp and resp.status_code == 200 else []

    async def get_item_full_detail(self, item_id: str):
        path = f"/Users/{self.user_id}/Items/{item_id}" if self.user_id else f"/Items/{item_id}"
        resp = await self._request("GET", path, params={"Fields": "Tags,TagItems,LockedFields,ProviderIds,Name"})
        return resp.json() if resp and resp.status_code == 200 else None

    async def update_item_metadata(self, item_id: str, tags_to_set: List[str], mode: str = 'merge') -> bool:
        """核心更新逻辑"""
        item_data = await self.get_item_full_detail(item_id)
        if not item_data: return False
        
        item_name = item_data.get("Name", "Unknown")
        original_tags = self._extract_tags(item_data)
        logger.info(f"┃  ┃  🔍 [解析] {item_name} 当前存量标签: {original_tags}")

        if mode == 'merge':
            final_tags = sorted(list(set(original_tags + tags_to_set)))
        else: # overwrite
            final_tags = sorted(list(set(tags_to_set)))
            
        if sorted(original_tags) == final_tags:
            logger.info(f"┃  ┃  🟡 标签无变动，跳过: {item_name}")
            return True
            
        item_data['Tags'] = final_tags
        item_data['TagItems'] = [{"Name": t} for t in final_tags]
        
        locked = item_data.get("LockedFields", [])
        if "Tags" in locked:
            item_data["LockedFields"] = [f for f in locked if f != "Tags"]
            
        resp = await self._request("POST", f"/Items/{item_id}", json_data=item_data)
        if resp and resp.status_code in [200, 204]:
            logger.info(f"🏷️ [成功] 已同步至 Emby: {item_name} -> {final_tags}")
            return True
        return False

    async def remove_specific_tags(self, item_id: str, tags_to_remove: List[str]) -> bool:
        """针对性的标签移除逻辑"""
        item_data = await self.get_item_full_detail(item_id)
        if not item_data: return False
        
        item_name = item_data.get("Name", "Unknown")
        original_tags = self._extract_tags(item_data)
        
        new_tags = [t for t in original_tags if t not in tags_to_remove]
        
        if sorted(original_tags) == sorted(new_tags):
            logger.info(f"┃  ┃  🟡 项目不含目标标签，跳过: {item_name}")
            return True
            
        return await self.update_item_metadata(item_id, new_tags, mode='overwrite')