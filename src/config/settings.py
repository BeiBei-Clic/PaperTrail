"""应用配置管理"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # DeepSeek API 配置
    deepseek_api_key: str = Field(default="", description="DeepSeek API Key")
    deepseek_model: str = Field(default="deepseek-chat", description="DeepSeek 模型名称")
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1", description="DeepSeek API 基础 URL")

    # LangChain 配置
    langchain_tracing_v2: bool = Field(default=False, description="是否启用 LangChain 追踪")
    langchain_api_key: str = Field(default="", description="LangChain API Key")
    langchain_project: str = Field(default="PageIndex-KB", description="LangChain 项目名称")

    # LLM 参数
    llm_temperature: float = Field(default=0.0, description="LLM 温度参数")
    max_tokens: int = Field(default=4096, description="最大 token 数")
    request_timeout: int = Field(default=120, description="请求超时时间（秒）")

    # 数据库配置
    database_url: str = Field(default="sqlite:///./data/knowledge_base.db", description="数据库连接 URL")

    # 文件存储
    storage_path: str = Field(default="./data/documents", description="文件存储路径")
    max_file_size: int = Field(default=104857600, description="最大文件大小（100MB）")

    # PageIndex 配置
    toc_check_page_num: int = Field(default=20, description="目录检查页数")
    max_page_num_each_node: int = Field(default=10, description="每个节点最大页数")
    max_token_num_each_node: int = Field(default=20000, description="每个节点最大 token 数")
    if_add_node_id: str = Field(default="yes", description="是否添加节点 ID")
    if_add_node_summary: str = Field(default="yes", description="是否添加节点摘要")
    if_add_doc_description: str = Field(default="yes", description="是否添加文档描述")
    if_add_node_text: str = Field(default="no", description="是否添加节点文本")

    # 检索配置
    default_top_k: int = Field(default=5, description="默认返回结果数")
    max_context_tokens: int = Field(default=16000, description="最大上下文 token 数")
    search_temperature: float = Field(default=0.3, description="搜索时的温度参数")

    # API 配置
    api_host: str = Field(default="0.0.0.0", description="API 服务主机")
    api_port: int = Field(default=8000, description="API 服务端口")
    api_reload: bool = Field(default=False, description="是否自动重载")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="./logs/knowledge_base.log", description="日志文件路径")

    # 项目路径
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_storage_path(self) -> Path:
        """获取文件存储路径"""
        path = Path(self.storage_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_log_path(self) -> Path:
        """获取日志文件路径"""
        path = Path(self.log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def get_db_path(self) -> Path:
        """获取数据库文件路径"""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            path = Path(db_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        return None


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    return _settings
