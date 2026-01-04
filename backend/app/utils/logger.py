import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import List, Dict, Any
import asyncio

# 日志根目录
LOG_DIR = "/app/data/logs"
os.makedirs(LOG_DIR, exist_ok=True)

class LogFormatter(logging.Formatter):
    """带颜色的控制台格式化"""
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: "%(asctime)s | 🔍 %(message)s",
        logging.INFO: blue + "%(asctime)s | %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s | ⚠️ %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s | ❌ %(message)s" + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "%(asctime)s | %(message)s")
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)

# 实时广播队列
log_queue = asyncio.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(log_queue.put(msg))
        except:
            pass

def setup_logger():
    logger = logging.getLogger("EmbyLens")
    logger.setLevel(logging.INFO)
    
    # 防止重复添加 Handler (工业级加固)
    if logger.handlers:
        return logger
    
    # 1. 控制台
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(LogFormatter())
    
    # 2. WebSocket 队列
    q_handler = QueueHandler()
    q_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S"))
    
    # 3. 按日持久化文件
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"{current_date}.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    
    logger.addHandler(stdout_handler)
    logger.addHandler(q_handler)
    logger.addHandler(file_handler)
    
    # 禁用日志向上传播，防止重复记录到 uvicorn 的 root logger
    logger.propagate = False
    
    return logger

logger = setup_logger()

# 辅助函数：模拟审计风格日志
def audit_log(title: str, duration_ms: float, details: List[str]):
    logger.info(f"⏱️ [性能审计]: {title} 耗时 {duration_ms:.0f}ms")
    logger.info(f"📢 [最终结论汇报]")
    for i, detail in enumerate(details):
        prefix = "┣" if i < len(details) - 1 else "┗"
        logger.info(f"{prefix} {detail}")

# 系统日志 API 相关逻辑
def get_log_dates() -> List[str]:
    """获取所有存在日志的日期列表"""
    files = [f.replace(".log", "") for f in os.listdir(LOG_DIR) if f.endswith(".log")]
    return sorted(files, reverse=True)

def get_log_content(date: str) -> str:
    """读取指定日期的完整日志文本"""
    path = os.path.join(LOG_DIR, f"{date}.log")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Log file not found."

def get_last_n_logs(n: int = 100) -> List[str]:
    """获取当前日志文件最后的 n 行，用于 WebSocket 初始化回填"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(LOG_DIR, f"{current_date}.log")
    if not os.path.exists(path):
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            # 简单实现：读取最后 n 行
            lines = f.readlines()
            return [line.strip() for line in lines[-n:]]
    except:
        return []
