"""主应用入口"""

import uvicorn

from src.api.app import app
from src.config.settings import get_settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """启动应用"""
    settings = get_settings()

    logger.info("启动 PageIndex 知识库系统...")
    logger.info(f"API 服务地址: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"API 文档: http://{settings.api_host}:{settings.api_port}/docs")

    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
