"""内容提取工具"""

from typing import Optional

from langchain_core.tools import tool


@tool
def content_extractor(node_id: str) -> dict:
    """
    提取指定文档节点的完整内容。

    Args:
        node_id: 节点ID

    Returns:
        节点的完整内容
    """
    from src.storage.database import get_session
    from src.storage.models import PageIndex

    with get_session() as session:
        node = session.query(PageIndex).filter(PageIndex.node_id == node_id).first()

        if not node:
            return {"error": f"节点不存在: {node_id}"}

        return {
            "node_id": node.node_id,
            "title": node.title,
            "summary": node.summary,
            "content": node.content,
            "page_start": node.page_start,
            "page_end": node.page_end,
            "level": node.level,
            "document_id": node.document_id,
        }


@tool
def get_document_structure(document_id: int) -> list:
    """
    获取文档的树状结构。

    Args:
        document_id: 文档ID

    Returns:
        文档的树状结构
    """
    from src.core.retrieval_engine import RetrievalEngine
    from src.storage.database import get_session

    with get_session() as session:
        retrieval_engine = RetrievalEngine(session)
        structure = retrieval_engine.get_document_structure(document_id)

        return structure


@tool
def get_node_path(node_id: str) -> list:
    """
    获取从根节点到指定节点的路径。

    Args:
        node_id: 节点ID

    Returns:
        节点路径列表
    """
    from src.core.tree_search import TreeSearchEngine
    from src.storage.database import get_session

    with get_session() as session:
        engine = TreeSearchEngine(session)
        path = engine.get_node_path(node_id)

        return [
            {
                "node_id": node.node_id,
                "title": node.title,
                "level": node.level,
            }
            for node in path
        ]
