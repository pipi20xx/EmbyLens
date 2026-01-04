from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class Tagger:
    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = rules

    def _parse_years(self, year_input: Any) -> List[int]:
        """1:1 复刻原版年份范围解析逻辑"""
        if not year_input: return []
        if isinstance(year_input, list): return [int(y) for y in year_input if str(y).isdigit()]
        
        years = []
        parts = str(year_input).replace(',', ' ').split()
        for part in parts:
            if '-' in part:
                match = re.match(r'(\d{4})-(\d{4})', part)
                if match:
                    start, end = map(int, match.groups())
                    years.extend(range(start, end + 1))
            elif part.isdigit():
                years.append(int(part))
        return list(set(years))

    def match_rule(self, item_props: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """
        1:1 源码级复刻匹配算法逻辑。
        """
        conditions = rule.get("conditions", {})
        item_type_limit = rule.get("item_type", "all")
        
        # 1. 检查类型 (Movie/Series)
        if item_type_limit != "all":
            it_map = {"movie": "Movie", "series": "Series"}
            if it_map.get(item_type_limit.lower()) != item_props.get("type"):
                return False
            
        match_all = rule.get("match_all_conditions", False)
        is_negative = rule.get("is_negative_match", False)
        
        # --- 核心算法：分项判定 ---
        
        results = []
        
        # 判定国家 (满足任一所选国家)
        if conditions.get("countries"):
            # 兼容：原项目可能匹配 ISO 代码也可能匹配中文名
            # 我们在 props 里准备了映射后的名称
            matched = any(c in item_props.get("countries", []) for c in conditions["countries"])
            results.append(matched)
            
        # 判定流派 (满足任一所选流派)
        if conditions.get("genres"):
            matched = any(g in item_props.get("genre_names", []) for g in conditions["genres"])
            results.append(matched)
            
        # 判定年份
        if conditions.get("years_text"):
            allowed = self._parse_years(conditions["years_text"])
            matched = item_props.get("year") in allowed if allowed else False
            results.append(matched)

        # --- 1:1 结果计算逻辑 ---
        if not results:
            final_match = False # 无条件不匹配
        elif match_all:
            final_match = all(results) # 必须全部命中定义的分类
        else:
            final_match = any(results) # 命中任一定义的分类即可

        # 负向匹配逻辑翻转
        return not final_match if is_negative else final_match

    def generate_tags(self, item_props: Dict[str, Any]) -> List[str]:
        tags = []
        for rule in self.rules:
            if self.match_rule(item_props, rule):
                tags.append(rule["tag"])
        return list(set(tags))