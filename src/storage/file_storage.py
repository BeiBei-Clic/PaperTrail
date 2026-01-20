"""文件存储管理"""

import hashlib
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from src.config.settings import get_settings


class FileStorage:
    """文件存储管理器"""

    def __init__(self):
        self.settings = get_settings()
        self.storage_path = self.settings.get_storage_path()

    def generate_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        # 获取文件扩展名
        ext = Path(original_filename).suffix
        # 生成唯一标识
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext}"

    def get_file_path(self, filename: str) -> Path:
        """获取文件的完整路径"""
        return self.storage_path / filename

    def save_file(self, file_content: bytes, filename: str) -> str:
        """保存文件到存储目录"""
        # 生成唯一文件名
        unique_filename = self.generate_filename(filename)
        file_path = self.get_file_path(unique_filename)

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        return unique_filename

    def save_file_from_path(self, source_path: str, filename: str) -> str:
        """从源路径复制文件到存储目录"""
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在: {source_path}")

        # 读取文件内容
        with open(source, "rb") as f:
            file_content = f.read()

        return self.save_file(file_content, filename)

    def delete_file(self, filename: str) -> bool:
        """删除文件"""
        file_path = self.get_file_path(filename)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        file_path = self.get_file_path(filename)
        return file_path.exists()

    def get_file_size(self, filename: str) -> int:
        """获取文件大小（字节）"""
        file_path = self.get_file_path(filename)
        if file_path.exists():
            return file_path.stat().st_size
        return 0

    def get_file_hash(self, filename: str, algorithm: str = "md5") -> str:
        """计算文件哈希值"""
        file_path = self.get_file_path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {filename}")

        hash_func = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def validate_file_size(self, file_content: bytes) -> bool:
        """验证文件大小是否符合限制"""
        return len(file_content) <= self.settings.max_file_size

    def get_all_files(self) -> list[str]:
        """获取所有存储的文件名"""
        if not self.storage_path.exists():
            return []

        return [f.name for f in self.storage_path.iterdir() if f.is_file()]

    def cleanup_orphaned_files(self, valid_filenames: list[str]) -> int:
        """清理孤立的文件（不在有效文件列表中的文件）"""
        all_files = set(self.get_all_files())
        valid_files = set(valid_filenames)
        orphaned = all_files - valid_files

        count = 0
        for filename in orphaned:
            if self.delete_file(filename):
                count += 1

        return count
