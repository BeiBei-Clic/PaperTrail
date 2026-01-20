"""检索引擎"""

from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from src.core.tree_search import TreeSearchEngine
from src.storage.models import PageIndex


class RetrievalEngine:
    """检索引擎"""

    def __init__(self, session: Session):
        self.session = session
        self.tree_search = TreeSearchEngine(session)

    def simple_search(self, query: str, doc_ids: Optional[List[int]] = None, top_k: int = 5) -> Dict[str, Any]:
        """简单搜索（不使用 Agent）"""
        nodes = self.tree_search.search_by_keywords(query, doc_ids, top_k)

        return {
            "query": query,
            "results": [
                {
                    "node_id": node.node_id,
                    "title": node.title,
                    "summary": node.summary,
                    "document_id": node.document_id,
                    "level": node.level,
                    "relevance_score": getattr(node, "relevance_score", 0),
                }
                for node in nodes
            ],
            "total": len(nodes),
        }

    def semantic_search(self, query: str, doc_ids: Optional[List[int]] = None, top_k: int = 5) -> Dict[str, Any]:
        """语义搜索（使用 LLM）"""
        nodes = self.tree_search.search_by_llm(query, doc_ids, top_k)

        return {
            "query": query,
            "results": [
                {
                    "node_id": node.node_id,
                    "title": node.title,
                    "summary": node.summary,
                    "document_id": node.document_id,
                    "level": node.level,
                    "relevance_score": getattr(node, "relevance_score", 0),
                }
                for node in nodes
            ],
            "total": len(nodes),
        }

    def get_node_content(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点完整内容"""
        from src.storage.models import PageIndex

        node = self.session.query(PageIndex).filter(PageIndex.node_id == node_id).first()

        if not node:
            return None

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

    def get_document_structure(self, doc_id: int) -> List[Dict[str, Any]]:
        """获取文档的树状结构"""
        from src.storage.models import PageIndex

        nodes = (
            self.session.query(PageIndex)
            .filter(PageIndex.document_id == doc_id)
            .order_by(PageIndex.level, PageIndex.node_id)
            .all()
        )

        # 构建树状结构
        node_map = {node.node_id: node.to_dict() for node in nodes}
        tree = []

        for node_dict in node_map.values():
            if node_dict["parent_id"]:
                parent = node_map.get(node_dict["parent_id"])
                if parent:
                    if "children" not in parent:
                        parent["children"] = []
                    parent["children"].append(node_dict)
            else:
                tree.append(node_dict)

        return tree
