"""基本功能测试"""

import os
import sys

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config.settings import get_settings
from src.storage.database import init_db, get_session
from src.storage.models import Document
from src.core.document_manager import DocumentManager


def test_config():
    """测试配置加载"""
    print("测试配置加载...")
    settings = get_settings()
    print(f"✓ DeepSeek 模型: {settings.deepseek_model}")
    print(f"✓ 数据库 URL: {settings.database_url}")
    print(f"✓ 存储路径: {settings.storage_path}")


def test_database():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    init_db()
    print("✓ 数据库初始化成功")

    with get_session() as session:
        document_manager = DocumentManager(session)
        count = document_manager.count_documents()
        print(f"✓ 当前文档数量: {count}")


def test_file_storage():
    """测试文件存储"""
    print("\n测试文件存储...")
    from src.storage.file_storage import FileStorage

    file_storage = FileStorage()
    storage_path = file_storage.get_storage_path()
    print(f"✓ 存储路径: {storage_path}")


def test_deepseek_client():
    """测试 DeepSeek 客户端"""
    print("\n测试 DeepSeek 客户端...")
    from src.adapters.deepseek_client import DeepSeekClient

    settings = get_settings()
    if not settings.deepseek_api_key or settings.deepseek_api_key == "your_deepseek_api_key_here":
        print("⚠ 跳过测试（未配置 API Key）")
        return

    client = DeepSeekClient()
    print(f"✓ DeepSeek 客户端初始化成功")
    print(f"✓ 模型: {settings.deepseek_model}")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("PageIndex 知识库系统 - 基本功能测试")
    print("=" * 60)

    try:
        test_config()
        test_database()
        test_file_storage()
        test_deepseek_client()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
