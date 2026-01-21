import os
import re
from typing import List, Set, Any

class BackupFilter:
    def __init__(self, ignore_patterns: List[str]):
        self.ignore_patterns = ignore_patterns
        # 将通配符转换为正则，例如 *.log -> .*
        self.regex_patterns = [self._wildcard_to_regex(p) for p in ignore_patterns]

    def _wildcard_to_regex(self, pattern: str) -> Any:
        """将简单的通配符转换为正则表达式"""
        # 处理路径分隔符
        p = pattern.replace('\\', '/')
        # 转义正则特殊字符，但保留 * 和 ?
        p = re.escape(p).replace(r'\*', '.*').replace(r'\?', '.')
        # 确保目录匹配逻辑：如果模式不含 /，则匹配文件名；如果含 /，则匹配路径
        if '/' not in pattern:
            return re.compile(f"(^|/){p}$", re.IGNORECASE)
        return re.compile(f"^{p}", re.IGNORECASE)

    def is_ignored(self, path: str, is_dir: bool = False) -> bool:
        """判断路径是否应该被忽略"""
        # 统一使用正斜杠
        path = path.replace('\\', '/')
        name = os.path.basename(path)
        
        for regex in self.regex_patterns:
            # 基础匹配：匹配文件名或全路径
            if regex.search(path) or regex.search(name):
                return True
        return False

    def generate_file_list(self, root_path: str, list_file_path: str) -> int:
        """
        递归扫描目录，生成待压缩文件清单。
        返回扫描到的文件总数。
        """
        count = 0
        # 确保 root_path 以斜杠结尾，以便正确生成相对路径
        root_path = os.path.abspath(root_path)
        base_dir = os.path.dirname(root_path)
        
        with open(list_file_path, 'w', encoding='utf-8') as f:
            for root, dirs, files in os.walk(root_path, topdown=True):
                # 实时修改 dirs 列表可以实现跳过整个文件夹的递归
                new_dirs = []
                for d in dirs:
                    d_path = os.path.join(root, d)
                    if not self.is_ignored(d_path, is_dir=True):
                        new_dirs.append(d)
                dirs[:] = new_dirs
                
                for file in files:
                    full_path = os.path.join(root, file)
                    if not self.is_ignored(full_path, is_dir=False):
                        # 7z 使用相对父目录的路径
                        rel_path = os.path.relpath(full_path, start=base_dir)
                        f.write(rel_path + '\n')
                        count += 1
        return count