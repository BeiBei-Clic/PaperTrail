"""
Configuration management for knowledge base system.
Uses Pydantic for settings validation and environment variable support.
"""

import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "PageIndex Knowledge Base"
    debug: bool = False
    version: str = "1.0.0"

    # Database
    database_url: str = "sqlite:///./data/knowledge_base.db"

    # File Storage
    storage_path: str = "./data/documents"
    max_file_size: int = 104857600  # 100MB in bytes

    # OpenAI API
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-2024-11-20"
    openai_base_url: Optional[str] = None  # For custom API endpoints

    # Retrieval Configuration
    default_top_k: int = 5
    max_context_tokens: int = 16000
    search_temperature: float = 0.3

    # Indexing Configuration
    toc_check_page_num: int = 20
    max_page_num_each_node: int = 10
    max_token_num_each_node: int = 20000
    if_add_node_id: str = "yes"
    if_add_node_summary: str = "yes"
    if_add_doc_description: str = "yes"
    if_add_node_text: str = "no"

    # Async Processing
    max_concurrent_indexing: int = 3
    indexing_timeout_seconds: int = 600  # 10 minutes

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/knowledge_base.log"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_directories()

    def _create_directories(self):
        """Create necessary directories."""
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(parents=True, exist_ok=True)
        Path("./logs").mkdir(parents=True, exist_ok=True)

    @property
    def is_configured(self) -> bool:
        """Check if essential configuration is present."""
        return bool(self.openai_api_key)

    def get_pageindex_config(self) -> dict:
        """
        Get configuration dict for PageIndex.

        Returns:
            Configuration dictionary for PageIndex
        """
        return {
            "model": self.openai_model,
            "toc_check_page_num": self.toc_check_page_num,
            "max_page_num_each_node": self.max_page_num_each_node,
            "max_token_num_each_node": self.max_token_num_each_node,
            "if_add_node_id": self.if_add_node_id,
            "if_add_node_summary": self.if_add_node_summary,
            "if_add_doc_description": self.if_add_doc_description,
            "if_add_node_text": self.if_add_node_text,
        }


# Global settings instance
_settings_instance = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.

    Returns:
        New Settings instance
    """
    global _settings_instance
    _settings_instance = Settings()
    return _settings_instance
