"""数据库连接和会话管理"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import get_settings
from src.storage.models import Base


def get_engine():
    """获取数据库引擎"""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    )


def get_session_factory():
    """获取会话工厂"""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 全局会话工厂
_session_factory = None


def get_session_factory_global():
    """获取全局会话工厂"""
    global _session_factory
    if _session_factory is None:
        _session_factory = get_session_factory()
    return _session_factory


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """获取数据库会话（上下文管理器）"""
    session_factory = get_session_factory_global()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """初始化数据库"""
    settings = get_settings()

    # 确保数据目录存在
    db_path = settings.get_db_path()
    if db_path:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建所有表
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    print(f"数据库初始化完成: {settings.database_url}")


def drop_all_tables():
    """删除所有表（危险操作，仅用于测试）"""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    print("所有表已删除")


def reset_db():
    """重置数据库（删除并重新创建）"""
    drop_all_tables()
    init_db()
