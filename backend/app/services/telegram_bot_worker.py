import asyncio
import httpx
from typing import List, Dict, Any
from app.core.config_manager import get_config
from app.services.docker_service import DockerService
from app.utils.logger import logger

class TelegramBotWorker:
    _tasks = {} # bot_id -> task

    @classmethod
    async def start_all(cls):
        """启动所有开启了交互功能的 Bot 监听"""
        config = get_config()
        bots = config.get("notification_settings", {}).get("bots", [])
        
        for bot in bots:
            if bot.get("enabled") and bot.get("is_interactive"):
                await cls.start_bot(bot)

    @classmethod
    async def start_bot(cls, bot_cfg: Dict):
        bot_id = bot_cfg.get("id")
        if bot_id in cls._tasks:
            cls._tasks[bot_id].cancel()
        
        # 启动前先同步菜单命令
        await cls._setup_bot_commands(bot_cfg)
        
        task = asyncio.create_task(cls._poll_loop(bot_cfg))
        cls._tasks[bot_id] = task
        logger.info(f"🤖 [TG Bot] 交互监听已启动: {bot_cfg.get('name')}")

    @classmethod
    async def _setup_bot_commands(cls, bot_cfg: Dict):
        """同步机器人菜单命令到 Telegram 服务器"""
        token = bot_cfg.get("token")
        url = f"https://api.telegram.org/bot{token}/setMyCommands"
        commands = [
            {"command": "hosts", "description": "查看 Docker 主机及容器列表"},
            {"command": "status", "description": "查看系统运行概览"},
            {"command": "start", "description": "重新显示欢迎消息"}
        ]
        
        try:
            config = get_config()
            proxy_url = config.get("proxy", {}).get("url") if config.get("proxy", {}).get("enabled") else None
            async with httpx.AsyncClient(proxies=proxy_url) as client:
                resp = await client.post(url, json={"commands": commands})
                if resp.status_code == 200:
                    logger.info(f"✅ [TG Bot] 菜单命令同步成功: {bot_cfg.get('name')}")
                else:
                    logger.warning(f"⚠️ [TG Bot] 菜单命令同步失败: {resp.text}")
        except Exception as e:
            logger.error(f"❌ [TG Bot] 同步菜单异常: {e}")

    @classmethod
    async def stop_bot(cls, bot_id: str):
        if bot_id in cls._tasks:
            cls._tasks[bot_id].cancel()
            del cls._tasks[bot_id]

    @classmethod
    async def _poll_loop(cls, bot_cfg: Dict):
        token = bot_cfg.get("token")
        offset = 0
        timeout = 30
        
        while True:
            try:
                config = get_config()
                proxy_url = config.get("proxy", {}).get("url") if config.get("proxy", {}).get("enabled") else None
                
                async with httpx.AsyncClient(timeout=timeout + 5, proxies=proxy_url) as client:
                    url = f"https://api.telegram.org/bot{token}/getUpdates"
                    params = {"offset": offset, "timeout": timeout}
                    
                    resp = await client.get(url, params=params)
                    
                    if resp.status_code != 200:
                        await asyncio.sleep(10)
                        continue
                        
                    data = resp.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        await cls._handle_update(bot_cfg, update)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ [TG Bot] 轮询异常 ({bot_cfg.get('name')}): {e}")
                await asyncio.sleep(10)

    @classmethod
    async def _handle_update(cls, bot_cfg: Dict, update: Dict):
        if "message" in update:
            msg = update["message"]
            chat_id = str(msg["chat"]["id"])
            user_id = str(msg["from"]["id"])
            text = msg.get("text", "")

            if user_id not in bot_cfg.get("allowed_user_ids", []):
                logger.warning(f"⚠️ [TG Bot] 未授权访问: User={user_id}, Name={msg['from'].get('first_name')}, Text={text}")
                return

            if text == "/start":
                await cls._send_message(bot_cfg, chat_id, "👋 你好！我是 Lens 管理助手。\n\n你可以使用以下指令：\n/hosts - 查看 Docker 主机列表\n/status - 查看系统概览")
            elif text == "/status":
                await cls._handle_status(bot_cfg, chat_id)
            elif text == "/hosts":
                await cls._handle_hosts(bot_cfg, chat_id)
        
        elif "callback_query" in update:
            user_id = str(update["callback_query"]["from"]["id"])
            if user_id not in bot_cfg.get("allowed_user_ids", []):
                return
            await cls._handle_callback(bot_cfg, update["callback_query"])

    @classmethod
    async def _handle_callback(cls, bot_cfg: Dict, query: Dict):
        data = query["data"]
        chat_id = query["message"]["chat"]["id"]
        query_id = query["id"]
        
        logger.info(f"🖱️ [TG Bot] 收到回调指令: {data}")
        await cls._answer_callback(bot_cfg, query_id)

        try:
            if data.startswith("hl:"):
                host_id = data.split(":")[1]
                await cls._show_containers(bot_cfg, chat_id, host_id)
            elif data.startswith("ci:"):
                parts = data.split(":")
                if len(parts) == 3:
                    host_id, container_id = parts[1], parts[2]
                    await cls._show_container_detail(bot_cfg, chat_id, host_id, container_id)
            elif data.startswith("co:"):
                parts = data.split(":")
                if len(parts) == 4:
                    host_id, container_id, op = parts[1], parts[2], parts[3]
                    await cls._exec_container_op(bot_cfg, chat_id, host_id, container_id, op)
            elif data == "hl_back":
                await cls._handle_hosts(bot_cfg, chat_id)
        except Exception as e:
            logger.error(f"❌ [TG Bot] 回调处理失败: {e}")
            await cls._send_message(bot_cfg, chat_id, f"❌ 操作执行出错: {str(e)}")

    @classmethod
    async def _handle_status(cls, bot_cfg: Dict, chat_id: str):
        config = get_config()
        hosts = config.get("docker_hosts", [])
        msg = "📊 *Docker 系统概览*\n\n"
        for h in hosts:
            try:
                service = DockerService(h)
                containers = service.list_containers()
                running = len([c for c in containers if c["status"] == "running"])
                msg += f"🖥 `{h['name']}`\n容器: {running} 运行中 / {len(containers)} 总计\n\n"
            except:
                msg += f"🖥 `{h['name']}`: ❌ 连接失败\n\n"
        await cls._send_message(bot_cfg, chat_id, msg)

    @classmethod
    async def _handle_hosts(cls, bot_cfg: Dict, chat_id: str):
        config = get_config()
        hosts = config.get("docker_hosts", [])
        buttons = []
        for h in hosts:
            buttons.append([{"text": f"🖥 {h['name']}", "callback_data": f"hl:{h['id']}"}])
        await cls._send_message(bot_cfg, chat_id, "请选择要管理的主机：", reply_markup={"inline_keyboard": buttons})

    @classmethod
    async def _show_containers(cls, bot_cfg: Dict, chat_id: str, host_id: str):
        config = get_config()
        host = next((h for h in config.get("docker_hosts", []) if h["id"] == host_id), None)
        if not host: 
            logger.error(f"❌ [TG Bot] 找不到主机配置: {host_id}")
            return
        
        logger.info(f"🔍 [TG Bot] 正在获取主机容器列表: {host.get('name')} ({host_id})")
        try:
            service = DockerService(host)
            containers = service.list_containers()
            # ... (保持原样)
            buttons = []
            for c in containers:
                status_icon = "🟢" if c["status"] == "running" else "🔴"
                buttons.append([{"text": f"{status_icon} {c['name']}", "callback_data": f"ci:{host_id}:{c['id']}"}])
            buttons.append([{"text": "⬅️ 返回主机列表", "callback_data": "hl_back"}])
            await cls._send_message(bot_cfg, chat_id, f"🖥 主机 *{host['name']}* 的容器列表：", reply_markup={"inline_keyboard": buttons})
        except Exception as e:
            logger.error(f"❌ [TG Bot] 获取容器列表失败: {e}")
            await cls._send_message(bot_cfg, chat_id, f"❌ 获取容器列表失败: {str(e)}")

    @classmethod
    async def _show_container_detail(cls, bot_cfg: Dict, chat_id: str, host_id: str, container_id: str):
        config = get_config()
        host = next((h for h in config.get("docker_hosts", []) if h["id"] == host_id), None)
        if not host: return
        
        logger.info(f"📦 [TG Bot] 正在获取容器详情: Host={host.get('name')}, Container={container_id}")
        try:
            service = DockerService(host)
            containers = service.list_containers()
            c = next((item for item in containers if item["id"] == container_id or item.get("full_id") == container_id), None)
            if not c:
                logger.warning(f"⚠️ [TG Bot] 找不到容器: {container_id}")
                await cls._send_message(bot_cfg, chat_id, "❌ 找不到该容器，可能已被删除或重命名。")
                return

            # 状态中文化
            status_map = {
                "running": "运行中 (Running)",
                "exited": "已停止 (Exited)",
                "paused": "已暂停 (Paused)",
                "restarting": "正在重启 (Restarting)",
                "created": "已创建 (Created)",
                "dead": "已损坏 (Dead)"
            }
            display_status = status_map.get(c["status"].lower(), c["status"])

            msg = f"📦 *容器详情*\n\n名称: `{c['name']}`\n镜像: `{c['image']}`\n状态: `{display_status}`\nID: `{c['id']}`"
            
            buttons = []
            if c["status"] == "running":
                buttons.append([
                    {"text": "🛑 停止", "callback_data": f"co:{host_id}:{container_id}:stop"},
                    {"text": "🔄 重启", "callback_data": f"co:{host_id}:{container_id}:restart"}
                ])
            else:
                buttons.append([{"text": "▶️ 启动", "callback_data": f"co:{host_id}:{container_id}:start"}])
            
            buttons.append([{"text": "🆙 更新容器 (Pull & Recreate)", "callback_data": f"co:{host_id}:{container_id}:update"}])
            buttons.append([
                {"text": "🔄 刷新详情", "callback_data": f"ci:{host_id}:{container_id}"},
                {"text": "⬅️ 返回列表", "callback_data": f"hl:{host_id}"}
            ])
            await cls._send_message(bot_cfg, chat_id, msg, reply_markup={"inline_keyboard": buttons})
        except Exception as e:
            logger.error(f"❌ [TG Bot] 获取详情失败: {e}")
            await cls._send_message(bot_cfg, chat_id, f"❌ 获取详情失败: {str(e)}")

    @classmethod
    async def _exec_container_op(cls, bot_cfg: Dict, chat_id: str, host_id: str, container_id: str, op: str):
        config = get_config()
        host = next((h for h in config.get("docker_hosts", []) if h["id"] == host_id), None)
        service = DockerService(host)
        
        # 记录容器名称，因为更新后 ID 会变
        container_name = None
        try:
            containers = service.list_containers()
            c_old = next((item for item in containers if item["id"] == container_id or item.get("full_id") == container_id), None)
            if c_old:
                container_name = c_old["name"]
        except: pass

        await cls._send_message(bot_cfg, chat_id, f"⏳ 正在执行 `{op}` 操作...")
        
        success = service.container_action(container_id, op)
        
        if success:
            await cls._send_message(bot_cfg, chat_id, f"✅ 操作 `{op}` 执行成功！")
            
            target_id = container_id
            # 如果是重构或更新，需要找到新的 ID
            if op in ["recreate", "update"] and container_name:
                try:
                    # 稍等一下让 Docker 状态同步
                    await asyncio.sleep(1)
                    new_containers = service.list_containers()
                    c_new = next((item for item in new_containers if item["name"] == container_name), None)
                    if c_new:
                        target_id = c_new["id"]
                        logger.info(f"🔄 [TG Bot] 容器 {container_name} ID 已更新: {container_id} -> {target_id}")
                except: pass
            
            # 使用新 ID 刷新详情页
            await cls._show_container_detail(bot_cfg, chat_id, host_id, target_id)
        else:
            await cls._send_message(bot_cfg, chat_id, f"❌ 操作 `{op}` 执行失败。")

    @staticmethod
    async def _send_message(bot_cfg: Dict, chat_id: str, text: str, reply_markup: Dict = None):
        token = bot_cfg.get("token")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        escaped_text = text
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f"\\{char}")
        payload = {"chat_id": chat_id, "text": escaped_text, "parse_mode": "MarkdownV2"}
        if reply_markup: payload["reply_markup"] = reply_markup
        try:
            config = get_config()
            proxy_url = config.get("proxy", {}).get("url") if config.get("proxy", {}).get("enabled") else None
            async with httpx.AsyncClient(proxies=proxy_url, timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    if "can't parse entities" in resp.text:
                        payload["parse_mode"] = None
                        payload["text"] = text
                        await client.post(url, json=payload)
        except Exception as e:
            logger.error(f"❌ [TG Bot] 发送消息异常: {e}")

    @staticmethod
    async def _answer_callback(bot_cfg: Dict, query_id: str):
        token = bot_cfg.get("token")
        url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
        try:
            config = get_config()
            proxy_url = config.get("proxy", {}).get("url") if config.get("proxy", {}).get("enabled") else None
            async with httpx.AsyncClient(proxies=proxy_url) as client:
                await client.post(url, json={"callback_query_id": query_id})
        except: pass