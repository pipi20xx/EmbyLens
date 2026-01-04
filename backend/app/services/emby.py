import httpx
import json
from typing import List, Dict, Any, Optional
from app.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models.media import MediaItem

class EmbyService:
    def __init__(self, url: str, api_key: str, user_id: str = None, tmdb_key: str = None):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.user_id = user_id
        self.tmdb_key = tmdb_key
        self.headers = {
            "X-Emby-Token": api_key,
            "Accept": "application/json"
        }

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=30.0, headers=self.headers)

    async def test_connection(self) -> bool:
        """测试与 Emby 服务器的连接"""
        try:
            async with self._get_client() as client:
                response = await client.get(f"{self.url}/emby/System/Info")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"连接 Emby 失败: {str(e)}")
            return False

    async def fetch_items(self, item_types: List[str], recursive: bool = True, parent_id: str = None) -> List[Dict[str, Any]]:
        """从 Emby 获取媒体项"""
        params = {
            "IncludeItemTypes": ",".join(item_types),
            "Recursive": str(recursive).lower(),
            "Fields": "Path,ProductionYear,ProviderIds,MediaStreams,DisplayTitle,SortName,Genres,GenreItems,LockedFields,LockData,People"
        }
        if parent_id:
            params["ParentId"] = parent_id
            
        try:
            async with self._get_client() as client:
                response = await client.get(f"{self.url}/emby/Items", params=params)
                response.raise_for_status()
                return response.json().get("Items", [])
        except Exception as e:
            logger.error(f"获取 Emby 媒体列表失败: {str(e)}")
            return []

    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取单个项目的元数据"""
        try:
            async with self._get_client() as client:
                # 优先使用带 UserID 的路径获取完整信息
                url = f"{self.url}/emby/Users/{self.user_id}/Items/{item_id}" if self.user_id else f"{self.url}/emby/Items/{item_id}"
                response = await client.get(url)
                return response.json() if response.status_code == 200 else None
        except: return None

        async def update_item(self, item_id: str, data: Dict[str, Any]) -> bool:

            """更新元数据并打印原始指令"""

            url = f"{self.url}/emby/Items/{item_id}"

            

            # 模拟生成 CURL 命令用于调试

            curl_cmd = f"curl -X POST '{url}' -H 'X-Emby-Token: {self.api_key}' -H 'Content-Type: application/json' -d '{json.dumps(data, ensure_ascii=False)}'"

            logger.info(f"🚀 发送 Emby 原始指令:")

            logger.info(f"┣ URL: {url}")

            logger.info(f"┗ CURL: {curl_cmd[:200]}...") # 日志中截断，防止刷屏

            

            try:

                async with self._get_client() as client:

                    response = await client.post(url, json=data)

                    return response.status_code in [200, 204]

            except Exception as e:

                logger.error(f"指令发送失败: {str(e)}")

                return False

    