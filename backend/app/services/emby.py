import httpx
import json
from typing import List, Dict, Any, Optional
from app.utils.logger import logger

class EmbyService:
    def __init__(self, url: str, api_key: str, user_id: str = None, tmdb_key: str = None):
        self.url = url.rstrip('/')
        self.base_url = f"{self.url}/emby" # 严格对齐原版 BaseURL
        self.api_key = api_key
        self.user_id = user_id
        self.tmdb_key = tmdb_key
        self.headers = {
            "X-Emby-Token": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=30.0, headers=self.headers)

    async def _request(self, method: str, endpoint: str, params: Dict = None, json_data: Dict = None):
        """1:1 复刻 emby-box 的底层请求逻辑"""
        url = f"{self.base_url}{endpoint}"
        
        # 核心：必须在 URL 参数里带上 api_key
        full_params = {"api_key": self.api_key}
        if params:
            full_params.update(params)
            
        # 工业级透明调试
        logger.info(f"┃  ┣ 🚀 [API 执行] {method} {url}")
        if json_data:
            # 缩减 payload 显示，防止日志爆炸，但保留核心字段
            payload_peek = {k: v for k, v in json_data.items() if k in ["Genres", "GenreItems", "LockedFields", "LockData", "People"]}
            logger.info(f"┃  ┃  📦 Payload: {payload_peek}")

        try:
            async with self._get_client() as client:
                response = await client.request(method, url, params=full_params, json=json_data)
                res_text = response.text if response.text else "(No Content)"
                logger.info(f"┃  ┃  📥 [Emby 响应] Status: {response.status_code} | Body: {res_text[:200]}")
                return response
        except Exception as e:
            logger.error(f"┃  ┃  ❌ 指令发送异常: {str(e)}")
            return None

    async def test_connection(self) -> bool:
        resp = await self._request("GET", "/System/Info")
        return resp is not None and resp.status_code == 200

    async def fetch_items(self, item_types: List[str], recursive: bool = True, parent_id: str = None) -> List[Dict[str, Any]]:
        params = {
            "IncludeItemTypes": ",".join(item_types),
            "Recursive": str(recursive).lower(),
            "Fields": "Path,ProductionYear,ProviderIds,MediaStreams,DisplayTitle,SortName,Genres,GenreItems,LockedFields,LockData,People"
        }
        if parent_id:
            params["ParentId"] = parent_id
            
        resp = await self._request("GET", "/Items", params=params)
        return resp.json().get("Items", []) if resp and resp.status_code == 200 else []

    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取单个项目的完整元数据 (强制全字段模式)"""
        full_fields = "ProviderIds,Name,Type,Id,Path,Overview,Genres,GenreItems,People,LockedFields,LockData,ChannelMappingInfo,MediaSources,MediaStreams"
        params = {"Fields": full_fields}
        try:
            async with self._get_client() as client:
                url = f"{self.url}/emby/Users/{self.user_id}/Items/{item_id}" if self.user_id else f"{self.url}/emby/Items/{item_id}"
                response = await client.get(url, params={**params, "api_key": self.api_key})
                return response.json() if response.status_code == 200 else None
        except:
            return None

    async def update_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """严格按照原版发送 POST 更新"""
        resp = await self._request("POST", f"/Items/{item_id}", json_data=data)
        return resp is not None and resp.status_code in [200, 204]

    async def delete_item(self, item_id: str) -> bool:
        """调用 Emby API 删除条目"""
        resp = await self._request("DELETE", f"/Items/{item_id}")
        return resp is not None and resp.status_code in [200, 204]
