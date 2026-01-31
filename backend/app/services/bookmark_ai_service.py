import json
import time
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.services.ai_service import AIService
from app.services.config_service import ConfigService
from app.services.bookmark_service import get_data, save_data
from app.utils.logger import logger

class BookmarkAIService:
    # 系统默认分类（兜底）
    DEFAULT_CATEGORIES = [
        "AI 与智能工具", "技术与开发", "设计与创意", "办公与效率", "影音与娱乐", 
        "动漫与游戏", "阅读与资讯", "生活与购物", "知识与教育", "其他归档"
    ]

    @classmethod
    async def run_auto_organize(cls, target_folder_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """全量日志 + 专家级清洗 + 严格拦截逻辑"""
        data = get_data()
        bookmarks = data.get("bookmarks", [])
        
        # 1. 获取最新分类预设
        categories = await ConfigService.get("ai_bookmark_categories", cls.DEFAULT_CATEGORIES)
        if not categories or not isinstance(categories, list):
            categories = cls.DEFAULT_CATEGORIES

        # 2. 扫描数据
        folder_map = {str(b["id"]): b["title"] for b in bookmarks if b["type"] == "folder"}
        
        target_ids = None
        if target_folder_id and target_folder_id != 'root':
            target_ids = {target_folder_id}
            changed = True
            while changed:
                changed = False
                for b in bookmarks:
                    if b["type"] == "folder" and str(b.get("parent_id")) in target_ids:
                        if str(b["id"]) not in target_ids:
                            target_ids.add(str(b["id"]))
                            changed = True
        
        all_files = []
        for b in bookmarks:
            if b.get("type") == "file":
                pid = str(b.get("parent_id"))
                if target_ids and pid not in target_ids and str(b["id"]) != target_folder_id:
                    continue
                
                parent_name = folder_map.get(pid, "根目录")
                all_files.append({
                    "id": b["id"],
                    "title": b["title"],
                    "url": b.get("url", ""),
                    "current_folder": parent_name
                })
        
        total = len(all_files)
        if total == 0:
            yield "未找到待处理的书签。"
            return

        yield f"🚀 [启动] 总计待处理书签: {total}，目标分类数: {len(categories)}"
        logger.info(f"🤖 [AI书签整理] 专家模式+严格限制启动，总数: {total}")

        # 3. 分批处理
        BATCH_SIZE = 20 
        for i in range(0, total, BATCH_SIZE):
            batch = all_files[i:i + BATCH_SIZE]
            current_range = f"{i+1}-{min(i+BATCH_SIZE, total)}"
            
            yield f"正在分析第 {current_range} 个书签..."
            logger.info(f"🛰️ [AI请求] 正在深度处理批次: {current_range}")
            
            prompt = f"""
            # Role
            你是一位拥有极致审美和强迫症逻辑的书签整理专家。
            
            # STRICT LIMIT (强制约束)
            你【只能】将书签归类到以下提供的分类名中：
            ---
            {', '.join(categories)}
            ---
            【严禁】创建任何新分类名。如果不确定，请统一分配到“其他归档”中。
            
            # Task
            对下方的书签进行【语义化标题清洗】和【强制精准归类】。
            
            # Rules
            1. **深度标题清洗**：
               - 移除所有冗余后缀（如：- 首页, | 知乎, _CSDN博客, - 官网, - 哔哩哔哩）。
               - 语义化重构：如果原标题晦涩（如纯URL），请根据 URL 语义起一个直观的中文名。
               - 保持简洁：最终标题建议控制在 10 个中文字符以内。
               - 品牌保护：保留核心品牌名（如：GitHub, Docker, Emby, Steam, ChatGPT）。
            2. **强制归类**：
               - 每一个书签 ID 必须分配一个来自上述列表的分类。
            
            # Data
            {json.dumps(batch, ensure_ascii=False)}
            
            # Output (Strict JSON)
            {{
              "updates": {{
                 "ID": {{ "folder": "分类名", "title": "新标题" }}
              }}
            }}
            """
            
            try:
                response_text = await AIService.chat_json([
                    {"role": "system", "content": "你只返回 JSON。严禁创建新分类。"},
                    {"role": "user", "content": prompt}
                ])
                
                clean_json = response_text.strip()
                if clean_json.startswith("```"):
                    clean_json = clean_json.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                if clean_json.startswith("json"):
                    clean_json = clean_json[4:].strip()

                suggestions = json.loads(clean_json)
                
                # --- 后端强力拦截逻辑 ---
                updates = suggestions.get("updates", {})
                for b_id, info in updates.items():
                    target_f = info.get("folder")
                    if target_f not in categories:
                        logger.warning(f"🛡️ [拦截] AI 尝试创建分类 '{target_f}'，已强制重定向至 '其他归档'")
                        info["folder"] = "其他归档"
                
                suggestions["folders"] = categories
                cls._apply_batch(suggestions)
                
                # 颗粒化日志输出
                for b_id, info in updates.items():
                    orig = next((b for b in batch if str(b['id']) == b_id), None)
                    orig_name = orig['title'] if orig else "未知"
                    msg = f"📍 [{info['folder']}] {orig_name} -> {info['title']}"
                    yield msg
                    logger.info(f"✨ [AI] {msg}")
                
            except Exception as e:
                err_msg = f"⚠️ 处理批次 {current_range} 出错: {str(e)}"
                yield err_msg
                logger.error(f"❌ [AI整理错误] {err_msg}")

        yield "🧹 正在收尾：递归清理旧空目录..."
        cls._recursive_cleanup()
        
        yield "🎉 任务完成！书签树已成功规范化。"
        logger.info("🎉 [AI书签整理] 全流程结束。")

    @classmethod
    def _apply_batch(cls, suggestions: Dict):
        data = get_data()
        bookmarks = data.get("bookmarks", [])
        now_ms = int(time.time() * 1000)
        
        folder_name_to_id = {b["title"]: str(b["id"]) for b in bookmarks if b["type"] == "folder"}
        
        for f_name in suggestions.get("folders", []):
            if f_name not in folder_name_to_id:
                f_id = f"bm_ai_fld_{now_ms}_{f_name}"
                bookmarks.append({
                    "id": f_id, "type": "folder", "title": f_name, "parent_id": None, "order": 0
                })
                folder_name_to_id[f_name] = f_id
        
        updates = suggestions.get("updates", {})
        for i, bm in enumerate(bookmarks):
            bm_id = str(bm["id"])
            if bm_id in updates:
                info = updates[bm_id]
                bookmarks[i]["title"] = info.get("title", bm["title"])
                target_f = info.get("folder")
                if target_f in folder_name_to_id:
                    bookmarks[i]["parent_id"] = folder_name_to_id[target_f]
        
        save_data(data)

    @classmethod
    def _recursive_cleanup(cls):
        data = get_data()
        def do_cleanup():
            bookmarks = data.get("bookmarks", [])
            used_ids = {str(b.get("parent_id")) for b in bookmarks if b.get("parent_id")}
            new_list = []
            removed = 0
            for b in bookmarks:
                if b["type"] == "folder" and str(b["id"]) not in used_ids:
                    removed += 1
                    continue
                new_list.append(b)
            data["bookmarks"] = new_list
            return removed
        while True:
            if do_cleanup() == 0: break
        save_data(data)