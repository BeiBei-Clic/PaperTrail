"""树搜索工具"""

import re
from typing import List, Optional

from sqlalchemy.orm import Session

from src.adapters.langchain_adapter import LangChainPageIndexAdapter
from src.config.prompts import PromptTemplates
from src.config.settings import get_settings
from src.storage.models import PageIndex


class TreeSearchEngine:
    """树搜索引擎"""

    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()
        self.adapter = LangChainPageIndexAdapter()

    def search_by_keywords(
        self, query: str, doc_ids: Optional[List[int]] = None, top_k: int = 5
    ) -> List[PageIndex]:
        """基于关键词搜索"""
        query_builder = self.session.query(PageIndex)

        if doc_ids:
            query_builder = query_builder.filter(PageIndex.document_id.in_(doc_ids))

        # 在标题和摘要中搜索关键词
        keyword = f"%{query}%"
        nodes = (
            query_builder.filter(
                (PageIndex.title.like(keyword)) | (PageIndex.summary.like(keyword))
            )
            .all()
        )

        for node in nodes:
            node.relevance_score = self._calculate_keyword_relevance(query, node)

        nodes.sort(key=lambda n: (-n.relevance_score, n.level))
        return nodes[:top_k]

    def search_by_llm(
        self, query: str, doc_ids: Optional[List[int]] = None, top_k: int = 5
    ) -> List[PageIndex]:
        """基于 LLM 语义搜索"""
        # 获取候选节点
        query_builder = self.session.query(PageIndex)

        if doc_ids:
            query_builder = query_builder.filter(PageIndex.document_id.in_(doc_ids))

        # 获取所有候选节点
        all_nodes = query_builder.all()

        if not all_nodes:
            return []

        # 使用 LLM 评估相关性
        scored_nodes = []
        for node in all_nodes:
            score = self._calculate_relevance(query, node)
            if score > 0:
                node.relevance_score = score
                scored_nodes.append(node)

        # 按相关性排序并返回 top_k
        scored_nodes.sort(key=lambda n: n.relevance_score, reverse=True)
        return scored_nodes[:top_k]

    def _calculate_relevance(self, query: str, node: PageIndex) -> float:
        """计算查询与节点的相关性分数"""
        prompt = PromptTemplates.get_retrieval_prompt("semantic_search").format(
            query=query,
            title=node.title,
            summary=node.summary or "",
        )

        result = self.adapter.call_llm(self.settings.deepseek_model, prompt, temperature=0.1)

        # 解析分数（假设返回 "分数：8" 或类似格式）
        match = re.search(r"(\d+(?:\.\d+)?)", result)
        if match:
            score = float(match.group(1))
            return min(score / 10.0, 1.0)  # 归一化到 0-1

        return 0.0

    def _calculate_keyword_relevance(self, query: str, node: PageIndex) -> float:
        query_text = query.strip().lower()
        if not query_text:
            return 0.0

        title_text = (node.title or "").lower()
        summary_text = (node.summary or "").lower()

        terms = [term for term in re.split(r"\s+", query_text) if term]
        max_score = 0.0
        score = 0.0

        for term in terms:
            max_score += 3.0
            if term in title_text:
                score += 2.0
            if term in summary_text:
                score += 1.0

        max_score += 3.0
        if query_text in title_text:
            score += 2.0
        if query_text in summary_text:
            score += 1.0

        if max_score == 0:
            return 0.0

        return min(score / max_score, 1.0)

    def get_node_path(self, node_id: str) -> List[PageIndex]:
        """获取节点路径（从根到当前节点）"""
        path = []
        current = self.session.query(PageIndex).filter(PageIndex.node_id == node_id).first()

        while current:
            path.insert(0, current)
            if current.parent_id:
                current = (
                    self.session.query(PageIndex)
                    .filter(PageIndex.node_id == current.parent_id)
                    .first()
                )
            else:
                break

        return path

    def get_node_children(self, node_id: str) -> List[PageIndex]:
        """获取子节点"""
        return (
            self.session.query(PageIndex)
            .filter(PageIndex.parent_id == node_id)
            .order_by(PageIndex.node_id)
            .all()
        )

    def get_node_siblings(self, node_id: str) -> List[PageIndex]:
        """获取兄弟节点"""
        node = self.session.query(PageIndex).filter(PageIndex.node_id == node_id).first()
        if not node or not node.parent_id:
            return []

        return (
            self.session.query(PageIndex)
            .filter(PageIndex.parent_id == node.parent_id, PageIndex.node_id != node_id)
            .order_by(PageIndex.node_id)
            .all()
        )
