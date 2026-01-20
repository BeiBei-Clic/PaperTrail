"""
File storage management for knowledge base documents.
Handles file operations and storage management.
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FileStorage:
    """
    Manages file storage for uploaded documents.
    """

    def __init__(self, storage_path: str = "./data/documents"):
        """
        Initialize file storage.

        Args:
            storage_path: Directory path for storing documents
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def get_file_path(self, filename: str) -> Path:
        """
        Get the full path for a file in storage.

        Args:
            filename: Name of the file

        Returns:
            Full path to the file
        """
        return self.storage_path / filename

    def save_file(self, source_path: str, filename: str) -> Path:
        """
        Save a file to storage.

        Args:
            source_path: Path to the source file
            filename: Name to save the file as

        Returns:
            Path to the saved file
        """
        dest_path = self.get_file_path(filename)
        shutil.copy2(source_path, dest_path)
        logger.info(f"File saved: {dest_path}")
        return dest_path

    def delete_file(self, filename: str):
        """
        Delete a file from storage.

        Args:
            filename: Name of the file to delete
        """
        file_path = self.get_file_path(filename)
        try:
            file_path.unlink()
            logger.info(f"File deleted: {file_path}")
        except FileNotFoundError:
            pass  # File doesn't exist, nothing to do

    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            filename: Name of the file

        Returns:
            True if file exists, False otherwise
        """
        return self.get_file_path(filename).exists()

    def get_file_size(self, filename: str) -> int:
        """
        Get the size of a file in bytes.

        Args:
            filename: Name of the file

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = self.get_file_path(filename)
        return file_path.stat().st_size

    def get_file_hash(self, filename: str) -> str:
        """
        Calculate MD5 hash of a file.

        Args:
            filename: Name of the file

        Returns:
            MD5 hash as hex string

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = self.get_file_path(filename)
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def list_files(self) -> list:
        """
        List all files in storage.

        Returns:
            List of filenames
        """
        return [f.name for f in self.storage_path.iterdir() if f.is_file()]

    def get_storage_size(self) -> int:
        """
        Get total size of all files in storage.

        Returns:
            Total size in bytes
        """
        total_size = 0
        for file_path in self.storage_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size

    def cleanup_storage(self):
        """
        Remove all files from storage.
        Use with caution!
        """
        for file_path in self.storage_path.iterdir():
            if file_path.is_file():
                file_path.unlink()
        logger.info(f"Storage cleaned: {self.storage_path}")
