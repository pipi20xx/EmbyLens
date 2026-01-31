import json
import time
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.services.ai_service import AIService
from app.services.config_service import ConfigService
from app.services.bookmark_service import get_data, save_data
from app.utils.logger import logger

class BookmarkAIService:
    @classmethod
    async def run_auto_organize(cls, target_folder_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """严格遵守用户预设分类的全自动流式整理"""
        data = get_data()
        bookmarks = data.get("bookmarks", [])
        
        # 1. 获取用户自定义的标准分类
        categories = await ConfigService.get("ai_bookmark_categories", [])
        if not categories:
            yield "❌ 错误：未配置标准分类列表，请先设置。"
            return

        # 2. 筛选待处理书签
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
            yield "未找到符合条件的书签。"
            return

        yield f"🚀 [AI启动] 准备规范化 {total} 个书签..."
        logger.info(f"🤖 [AI书签整理] 启动任务，总数: {total}, 分类数: {len(categories)}")

        # 3. 分批处理
        BATCH_SIZE = 20 
        for i in range(0, total, BATCH_SIZE):
            batch = all_files[i:i + BATCH_SIZE]
            current_range = f"{i+1}-{min(i+BATCH_SIZE, total)}"
            
            yield f"正在分析批次 {current_range}..."
            
            prompt = f"""
            你是一个书签管理与数据清洗专家。
            
            【绝对规则】：
            你【必须】将书签归类到以下指定的文件夹中，【严禁】创建任何不在列表中的文件夹：
            {", ".join(categories)}
            
            【任务要求】：
            1. 分类匹配：根据书签内容，从上述列表中选择一个【最相关】的分类。
            2. 标题清洗：去除冗余后缀（如“- 百度搜索”、“| 知乎”）。
            3. 每一个 ID 必须处理。
            
            待处理数据: {json.dumps(batch, ensure_ascii=False)}
            
            返回严格 JSON：
            {{
              "updates": {{ "ID": {{ "folder": "指定的分类名", "title": "清洗后的标题" }} }}
            }}
            """
            
            try:
                logger.info(f"🛰️ [AI请求] 批次 {current_range}...")
                response_text = await AIService.chat_json([
                    {"role": "system", "content": "你只返回 JSON 数据。"},
                    {"role": "user", "content": prompt}
                ])
                
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                
                suggestions = json.loads(response_text)
                # 将标准分类注入 suggestions 方便复用之前的 apply 逻辑
                suggestions["folders"] = categories
                
                cls._apply_batch(suggestions)
                
                updates = suggestions.get("updates", {})
                for b_id, info in updates.items():
                    orig = next((b for b in batch if str(b['id']) == b_id), None)
                    orig_name = orig['title'] if orig else "未知"
                    msg = f"📍 [{info['folder']}] {orig_name} -> {info['title']}"
                    yield msg
                    logger.info(f"✨ [AI整理] {msg}")
                
            except Exception as e:
                err_msg = f"⚠️ 批次 {current_range} 失败: {str(e)}"
                yield err_msg
                logger.error(f"❌ [AI整理错误] {err_msg}")

        yield "🧹 正在收尾，清理空文件夹..."
        cls._recursive_cleanup()
        
        yield "🎉 全自动整理已完成。"
        logger.info("🎉 [AI书签整理] 任务完成。")

    @classmethod
    def _apply_batch(cls, suggestions: Dict):
        data = get_data()
        bookmarks = data.get("bookmarks", [])
        now_ms = int(time.time() * 1000)
        
        folder_name_to_id = {b["title"]: str(b["id"]) for b in bookmarks if b["type"] == "folder"}
        
        # 1. 确保预设文件夹都存在（如果不存在则创建）
        for f_name in suggestions.get("folders", []):
            if f_name not in folder_name_to_id:
                f_id = f"bm_ai_fld_{now_ms}_{f_name}"
                bookmarks.append({
                    "id": f_id, "type": "folder", "title": f_name, "parent_id": None, "order": 0
                })
                folder_name_to_id[f_name] = f_id
        
        # 2. 更新书签
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
