import os
import shutil
import glob
from datetime import datetime
from app.utils.logger import logger

BACKUP_DIR = "data/backups/system_config"
MAX_VERSIONS = 20

def auto_backup_file(file_path: str, max_versions: int = MAX_VERSIONS):
    """
    自动备份文件并保留最近的 N 个版本
    :param file_path: 源文件路径 (如 data/config.json)
    :param max_versions: 保留的最大版本数
    """
    if not os.path.exists(file_path):
        return

    try:
        # 1. 确保备份目录存在
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # 2. 生成备份文件名
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        # 3. 执行复制
        shutil.copy2(file_path, backup_path)
        logger.info(f"🛡️ [AutoBackup] 已自动备份配置文件: {backup_name}")

        # 4. 执行轮转清理
        # 查找所有同名 pattern 的备份文件
        pattern = os.path.join(BACKUP_DIR, f"{name}_*{ext}")
        backups = glob.glob(pattern)
        
        # 按修改时间排序 (旧 -> 新)
        backups.sort(key=os.path.getmtime)
        
        # 如果超过限制，删除最旧的
        if len(backups) > max_versions:
            to_remove = backups[:len(backups) - max_versions]
            for f in to_remove:
                try:
                    os.remove(f)
                    logger.debug(f"🗑️ [AutoBackup] 清理旧备份: {os.path.basename(f)}")
                except Exception as e:
                    logger.warning(f"⚠️ [AutoBackup] 清理旧备份失败: {e}")

    except Exception as e:
        logger.error(f"❌ [AutoBackup] 备份失败 ({file_path}): {e}")
