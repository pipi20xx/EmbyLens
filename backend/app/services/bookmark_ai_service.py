import json
import time
import asyncio
from typing import List, Dict, Any, AsyncGenerator
from app.services.ai_service import AIService
from app.services.bookmark_service import get_data, save_data
from app.utils.logger import logger

class BookmarkAIService:
    @classmethod
    async def run_auto_organize(cls) -> AsyncGenerator[str, None]:
        """全自动流式整理：颗粒化日志 + 零阻塞执行"""
        data = get_data()
        bookmarks = data.get("bookmarks", [])
        
        folder_map = {str(b["id"]): b["title"] for b in bookmarks if b["type"] == "folder"}
        all_files = []
        for b in bookmarks:
            if b.get("type") == "file":
                parent_name = folder_map.get(str(b.get("parent_id")), "根目录")
                all_files.append({
                    "id": b["id"],
                    "title": b["title"],
                    "url": b.get("url", ""),
                    "current_folder": parent_name
                })
        
        total = len(all_files)
        if total == 0:
            yield "未找到任何书签。"
            return

        yield f"🚀 [AI开始] 总计待处理书签: {total}"
        logger.info(f"🤖 [AI书签整理] 启动任务，总数: {total}")

        BATCH_SIZE = 50
        for i in range(0, total, BATCH_SIZE):
            batch = all_files[i:i + BATCH_SIZE]
            
            prompt = f"""
            你是一个书签管理专家。请为以下书签分类并规范化标题。
            数据: {json.dumps(batch, ensure_ascii=False)}
            
            严格返回 JSON：
            {{
              "folders": ["分类名"],
              "updates": {{ "ID": {{ "folder": "分类名", "title": "规范标题" }} }}
            }}
            """
            
            try:
                response_text = await AIService.chat_json([
                    {"role": "system", "content": "你只返回 JSON。"},
                    {"role": "user", "content": prompt}
                ])
                
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                
                suggestions = json.loads(response_text)
                
                # 颗粒化处理：一条一条地应用并汇报
                cls._apply_item_by_item(suggestions, yield_func=None) # 这里内部会改写
                
                # 专门提取 updates 里的细节发给前端
                updates = suggestions.get("updates", {})
                for b_id, info in updates.items():
                    # 找到对应的原始书签标题
                    orig = next((b for b in batch if str(b['id']) == b_id), None)
                    orig_name = orig['title'] if orig else "未知"
                    msg = f"📍 [{info['folder']}] {orig_name} -> {info['title']}"
                    yield msg
                    logger.info(f"✨ [AI整理中] {msg}")
                
            except Exception as e:
                err_msg = f"⚠️ 处理批次 {i+1} 时出错: {str(e)}"
                yield err_msg
                logger.error(f"❌ [AI书签整理] {err_msg}")

        yield "🧹 正在自动清理旧的空文件夹..."
        cls._recursive_cleanup()
        
        yield "🎉 整理完成！书签树已刷新。"
        logger.info("🎉 [AI书签整理] 任务圆满结束。")

    @classmethod
    def _apply_item_by_item(cls, suggestions: Dict, yield_func=None):
        """内部执行函数"""
        data = get_data()
        bookmarks = data.get("bookmarks", [])
        now_ms = int(time.time() * 1000)
        
        folder_name_to_id = {}
        for f_name in suggestions.get("folders", []):
            existing = next((b for b in bookmarks if b["type"] == "folder" and b["title"] == f_name), None)
            if existing:
                folder_name_to_id[f_name] = existing["id"]
            else:
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
        """递归清理空文件夹"""
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