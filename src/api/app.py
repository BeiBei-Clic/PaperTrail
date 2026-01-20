"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.documents import router as documents_router
from src.api.routes.search import router as search_router
from src.config.settings import get_settings
from src.storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()

    # 启动时初始化数据库
    print("正在初始化数据库...")
    init_db()
    print("数据库初始化完成")

    yield

    # 关闭时的清理工作
    print("应用关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    settings = get_settings()

    app = FastAPI(
        title="PageIndex 知识库系统",
        description="基于 PageIndex 树状索引和 DeepSeek API 的知识库系统",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(documents_router, prefix="/api")
    app.include_router(search_router, prefix="/api")

    # 根路径
    @app.get("/")
    def read_root():
        return {
            "name": "PageIndex 知识库系统",
            "version": "0.1.0",
            "description": "基于 PageIndex 树状索引和 DeepSeek API 的知识库系统",
            "docs": "/docs",
        }

    # 健康检查
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}

    return app


# 创建应用实例
app = create_app()
