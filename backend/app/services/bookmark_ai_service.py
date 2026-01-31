import json
import time
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.services.ai_service import AIService
from app.services.bookmark_service import get_data, save_data
from app.utils.logger import logger

class BookmarkAIService:
    @classmethod
    async def run_auto_organize(cls, target_folder_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        全自动流式整理
        :param target_folder_id: 如果提供，则只处理该文件夹及其子文件夹下的书签
        """
        data = get_data()
        bookmarks = data.get("bookmarks", [])
        
        # 1. 筛选待处理书签
        folder_map = {str(b["id"]): b["title"] for b in bookmarks if b["type"] == "folder"}
        
        # 如果指定了文件夹，先找出该文件夹下的所有子孙文件夹 ID
        target_ids = None
        if target_folder_id and target_folder_id != 'root':
            target_ids = {target_folder_id}
            # 简单迭代查找所有子文件夹
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
                # 如果指定了目录，过滤不在该目录树下的书签
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

        yield f"🚀 [AI开始] 总计待处理书签: {total}"
        logger.info(f"🤖 [AI书签整理] 启动任务，总数: {total}, 目标目录: {target_folder_id or '全部'}")

        # 缩小批次大小，减少单次等待时间
        BATCH_SIZE = 20 
        for i in range(0, total, BATCH_SIZE):
            batch = all_files[i:i + BATCH_SIZE]
            current_range = f"{i+1}-{min(i+BATCH_SIZE, total)}"
            
            yield f"正在分析第 {current_range} 个书签 (AI 思考中...)"
            
            prompt = f"""
            你是一个书签管理专家。请为以下书签分类并规范化标题。
            数据: {json.dumps(batch, ensure_ascii=False)}
            
            要求：
            1. 文件夹名称精简。
            2. 标题去掉冗余后缀。
            3. 返回 JSON。
            
            返回格式：
            {{
              "folders": ["分类名"],
              "updates": {{ "ID": {{ "folder": "分类名", "title": "规范标题" }} }}
            }}
            """
            
            try:
                # 记录请求开始
                logger.info(f"🛰️ [AI请求] 正在分析批次 {current_range}...")
                
                response_text = await AIService.chat_json([
                    {"role": "system", "content": "你只返回 JSON。"},
                    {"role": "user", "content": prompt}
                ])
                
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                
                suggestions = json.loads(response_text)
                
                # 应用更改
                cls._apply_batch(suggestions)
                
                # 详细汇报
                updates = suggestions.get("updates", {})
                for b_id, info in updates.items():
                    orig = next((b for b in batch if str(b['id']) == b_id), None)
                    orig_name = orig['title'] if orig else "未知"
                    msg = f"📍 [{info['folder']}] {orig_name} -> {info['title']}"
                    yield msg
                    logger.info(f"✨ [AI整理] {msg}")
                
            except Exception as e:
                err_msg = f"⚠️ 处理批次 {current_range} 出错: {str(e)}"
                yield err_msg
                logger.error(f"❌ [AI整理错误] {err_msg}")

        yield "🧹 正在自动清理旧的空文件夹..."
        cls._recursive_cleanup()
        
        yield "🎉 整理完成！书签树已刷新。"
        logger.info("🎉 [AI书签整理] 任务圆满结束。")

    @classmethod
    def _apply_batch(cls, suggestions: Dict):
        data = get_data()
        bookmarks = data.get("bookmarks", [])
        now_ms = int(time.time() * 1000)
        
        # 建立当前最新文件夹标题到 ID 的映射
        folder_name_to_id = {b["title"]: str(b["id"]) for b in bookmarks if b["type"] == "folder"}
        
        # 1. 确保文件夹存在
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
