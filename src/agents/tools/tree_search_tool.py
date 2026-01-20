"""树搜索工具"""

from typing import Optional

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from src.config.prompts import PromptTemplates


@tool
def tree_search(
    query: str, doc_ids: Optional[list] = None, top_k: int = 5
) -> list:
    """
    在文档树结构中搜索相关节点。

    Args:
        query: 搜索查询
        doc_ids: 要搜索的文档ID列表（可选）
        top_k: 返回结果数量

    Returns:
        相关节点列表
    """
    from src.core.tree_search import TreeSearchEngine

    # 获取数据库会话
    from src.storage.database import get_session

    with get_session() as session:
        engine = TreeSearchEngine(session)
        nodes = engine.search_by_llm(query, doc_ids, top_k)

        return [
            {
                "node_id": node.node_id,
                "title": node.title,
                "summary": node.summary,
                "document_id": node.document_id,
                "level": node.level,
            }
            for node in nodes
        ]


@tool
def simple_tree_search(
    query: str, doc_ids: Optional[list] = None, top_k: int = 5
) -> list:
    """
    基于关键词在文档树结构中搜索相关节点（不使用 LLM）。

    Args:
        query: 搜索查询
        doc_ids: 要搜索的文档ID列表（可选）
        top_k: 返回结果数量

    Returns:
        相关节点列表
    """
    from src.core.tree_search import TreeSearchEngine

    from src.storage.database import get_session

    with get_session() as session:
        engine = TreeSearchEngine(session)
        nodes = engine.search_by_keywords(query, doc_ids, top_k)

        return [
            {
                "node_id": node.node_id,
                "title": node.title,
                "summary": node.summary,
                "document_id": node.document_id,
                "level": node.level,
            }
            for node in nodes
        ]
