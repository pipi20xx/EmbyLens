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
            "AI 智能工具",
            "编程与开发",
            "设计与素材",
            "办公与协作",
            "网络与安全",
            "服务器与 NAS",
            "在线工具箱",
            "软件与资源",
            "影视与流媒体",
            "动漫与二次元",
            "游戏与电竞",
            "音乐与音频",
            "资讯与阅读",
            "社区与论坛",
            "知识与百科",
            "生活与消费",
            "金融与资产",
            "未分类/其他"
        ]
    
        # 增强型分类指南（AI 提示词专用）
        CATEGORY_GUIDE = {
            "AI 智能工具": "ChatGPT, Midjourney, AI 绘画, 各种 AI 导航站, LLM 相关工具",
            "编程与开发": "GitHub, StackOverflow, 前端/后端/移动端开发文档, 编程框架官网, 技术博客",
            "设计与素材": "Dribbble, Behance, 花瓣, 字体下载, 图标库(Icon), 配色工具, UI/UX 资源",
            "办公与协作": "Notion, Google Docs, 飞书/钉钉, 邮箱服务, 在线表格, 团队协作工具, 简历制作",
            "网络与安全": "IP查询, 端口扫描, 代理工具, 域名注册, 网络测速, 内网穿透, SSL 证书",
            "服务器与 NAS": "Docker, Unraid, 群晖(Synology), 软路由(OpenWrt), Linux 运维命令, 容器管理(Portainer)",
            "在线工具箱": "PDF转换, 格式转换, 二维码生成, 临时文件分享, 计算器, 正则测试等轻量级工具",
            "软件与资源": "软件下载站, 破解资源, 镜像站(ISO), 脚本插件(Tampermonkey), 系统激活",
            "影视与流媒体": "Netflix, YouTube, 电影下载站(BT/PT), 字幕组, 在线看剧网站, 电视直播",
            "动漫与二次元": "B站(Bilibili), 番剧索引, 漫画阅读站, Pixiv, 模玩手办, 漫展资讯",
            "游戏与电竞": "Steam, Epic Games, 游戏攻略, 游戏资讯(IGN/G-Cores), Switch/PS5 社区",
            "音乐与音频": "Spotify, 网易云音乐, Apple Music, 有声书, 播客(Podcast), 音效素材下载",
            "资讯与阅读": "科技新闻(36Kr/少数派), 个人博客, RSS 订阅, 新闻门户, 技术周刊",
            "社区与论坛": "V2EX, Reddit, 百度贴吧, 专业的垂直领域论坛, 微信群/TG群导航",
            "知识与百科": "维基百科, 百度百科, 教程网(Runoob), 论文库(知网), 在线学习平台(Coursera/Udemy)",
            "生活与消费": "京东/淘宝/拼多多, 地图导航, 租房平台, 下厨房(菜谱), 旅行攻略(马蜂窝)",
            "金融与资产": "网银登录, 股市行情, 加密货币(交易所/行情), 记账工具, 理财论坛",
            "未分类/其他": "无法归类到以上任何类别的书签"
        }
    
        @classmethod
        async def run_auto_organize(cls, target_folder_id: Optional[str] = None) -> AsyncGenerator[str, None]:
            """全量日志 + 专家级分类逻辑"""
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
            logger.info(f"🤖 [AI书签整理] 启动，总数: {total}")
    
            # 3. 分批处理
            BATCH_SIZE = 20 
            for i in range(0, total, BATCH_SIZE):
                batch = all_files[i:i + BATCH_SIZE]
                current_range = f"{i+1}-{min(i+BATCH_SIZE, total)}"
                
                yield f"正在分析第 {current_range} 个书签..."
                logger.info(f"🛰️ [AI请求] 正在处理批次: {current_range}")
                
                prompt = f"""
                # Role
                你是一位精通信息架构的图书整理专家，擅长根据网站标题和URL分析其核心属性。
    
                # Goal
                请将提供的书签列表归类到【指定分类表】中最为精准的一个分类下。
    
                # 🧭 Category Guide (分类参考指南)
                请严格参考以下定义的分类标准进行判断：
                {json.dumps(cls.CATEGORY_GUIDE, ensure_ascii=False, indent=2)}
    
                # 📂 Allowed Categories (最终输出分类名)
                {json.dumps(categories, ensure_ascii=False)}
    
                # 🧪 Input Data (Bookmarks)
                {json.dumps(batch, ensure_ascii=False)}
    
                # ⚡ Rules (必须严格遵守)
                1. **核心逻辑**：优先分析 URL 的域名特征（如 github.com -> 编程，netflix.com -> 影视），其次结合标题语义。
                2. **强制匹配**：必须从“Allowed Categories”中选择一个最匹配的分类，严禁自创。
                3. **兜底策略**：如果无法确定或内容极其模糊，请归类为“未分类/其他”。
                4. **严禁修改**：保持书签的原始标题 (title) 不变。
                5. **格式要求**：输出纯粹的 JSON，不要包含 Markdown 代码块标记。
    
                # 📤 Output Format
                {{
                  "updates": {{
                     "<BOOKMARK_ID>": {{ "folder": "<EXACT_CATEGORY_NAME>" }},
                     ...
                  }}
                }}
                """
            
            try:
                response_text = await AIService.chat_json([
                    {"role": "system", "content": "你只返回 JSON。严禁修改标题，严禁创建新分类。"},
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
                        logger.warning(f"🛡️ [拦截] AI 尝试创建分类 '{target_f}'，已强制重定向至 '未分类/其他'")
                        info["folder"] = "未分类/其他"
                
                suggestions["folders"] = categories
                cls._apply_batch(suggestions)
                
                # 颗粒化日志输出
                for b_id, info in updates.items():
                    orig = next((b for b in batch if str(b['id']) == b_id), None)
                    orig_name = orig['title'] if orig else "未知"
                    msg = f"📍 [{info['folder']}] {orig_name}"
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