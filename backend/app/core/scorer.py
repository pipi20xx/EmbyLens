from typing import List, Dict, Any, Tuple
from app.utils.logger import logger

class Scorer:
    def __init__(self, rule: Dict[str, Any]):
        """
        rule 格式示例:
        {
            "priority_order": ["display_title", "video_codec", "video_range"],
            "values_weight": {
                "display_title": ["4k", "2160p", "1080p", "720p"],
                "video_codec": ["hevc", "h264", "av1"],
                "video_range": ["hdr", "dolbyvision", "sdr"]
            },
            "tie_breaker": "small_id"
        }
        """
        self.priority_order = rule.get("priority_order", [])
        self.values_weight = rule.get("values_weight", {})
        self.tie_breaker = rule.get("tie_breaker", "small_id")

    def get_value_score(self, crit: str, value: str) -> int:
        if not value:
            return 999
        
        priority_list = self.values_weight.get(crit, [])
        val_lower = str(value).lower()
        
        # 对于 display_title (媒体规格)，通常包含关键词匹配
        if crit == "display_title":
            for i, keyword in enumerate(priority_list):
                if keyword.lower() in val_lower:
                    return i
            return 999
            
        # 对于编码等精确匹配
        try:
            return priority_list.index(val_lower)
        except ValueError:
            return 999

    def score_item(self, item: Dict[str, Any]) -> Tuple[Tuple[int, ...], int]:
        """
        返回一个元组用于排序: (分数元组, ID权重)
        分数越小越优先（符合 Python sort 默认升序逻辑）
        """
        scores = []
        for crit in self.priority_order:
            val = item.get(crit)
            scores.append(self.get_value_score(crit, val))
        
        emby_id = item.get("emby_id", "0")
        # 处理 ID 排序逻辑
        try:
            id_val = int(emby_id)
        except:
            id_val = 0
            
        if self.tie_breaker == "large_id":
            id_weight = -id_val
        else:
            id_weight = id_val
            
        return tuple(scores), id_weight

    def select_best(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        输入一组重复项，返回建议删除的 ID 列表 (排除掉评分最高的一个)
        """
        if len(items) <= 1:
            return []
            
        # 按照 (分数元组, ID权重) 排序
        # 分数元组越小说明优先级越高
        scored_items = []
        for item in items:
            score, id_weight = self.score_item(item)
            scored_items.append({
                "id": item.get("emby_id"),
                "score_key": (score, id_weight)
            })
            
        scored_items.sort(key=lambda x: x["score_key"])
        
        # 排除第一个（最好的），剩下的都是建议删除的
        return [item["id"] for item in scored_items[1:]]
