"""索引引擎（集成 PageIndex）"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from src.adapters.langchain_adapter import LangChainPageIndexAdapter
from src.config.settings import get_settings
from src.core.document_manager import DocumentManager
from src.storage.models import Document, PageIndex


class IndexEngine:
    """索引引擎"""

    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()
        self.document_manager = DocumentManager(session)
        self.adapter = LangChainPageIndexAdapter()

    def index_document(self, doc_id: int) -> Optional[Document]:
        """索引文档"""
        document = self.document_manager.get_document(doc_id)
        if not document:
            raise ValueError(f"文档不存在: {doc_id}")

        # 更新状态为索引中
        self.document_manager.update_document_status(doc_id, "indexing")

        try:
            # 注入 DeepSeek API 到 PageIndex
            self.adapter.inject_to_pageindex()

            # 根据文档类型索引
            if document.doc_type == "pdf":
                tree_data = self._index_pdf(document)
            elif document.doc_type == "markdown":
                tree_data = self._index_markdown(document)
            else:
                raise ValueError(f"不支持的文档类型: {document.doc_type}")

            # 保存到数据库
            self._save_tree_data(document.id, tree_data)

            # 更新状态为已索引
            self.document_manager.update_document_status(doc_id, "indexed")

            return document

        except Exception as e:
            # 更新状态为失败
            self.document_manager.update_document_status(doc_id, "failed")
            raise e

    def _index_pdf(self, document: Document) -> dict:
        """索引 PDF 文档"""
        file_path = self.document_manager.get_document_file_path(document.id)

        # 创建配置对象，使用 PageIndex 默认配置并覆盖用户配置
        from pageindex.utils import ConfigLoader

        toc_check_page_num = (
            self.settings.toc_check_page_num
            if self.settings.toc_check_page_num is not None
            else 20
        )
        max_page_num_each_node = (
            self.settings.max_page_num_each_node
            if self.settings.max_page_num_each_node is not None
            else 10
        )
        max_token_num_each_node = (
            self.settings.max_token_num_each_node
            if self.settings.max_token_num_each_node is not None
            else 20000
        )

        user_opt = {
            "model": self.settings.deepseek_model,
            "toc_check_page_num": int(toc_check_page_num),
            "max_page_num_each_node": int(max_page_num_each_node),
            "max_token_num_each_node": int(max_token_num_each_node),
            "if_add_node_id": self.settings.if_add_node_id,
            "if_add_node_summary": self.settings.if_add_node_summary,
            "if_add_doc_description": self.settings.if_add_doc_description,
            "if_add_node_text": self.settings.if_add_node_text,
        }

        opt = ConfigLoader().load(user_opt)

        # 使用 PageIndex 索引 PDF
        from pageindex.page_index import page_index_main

        result = page_index_main(str(file_path), opt)
        tree_data = asyncio.run(result) if asyncio.iscoroutine(result) else result
        return tree_data

    def _index_markdown(self, document: Document) -> dict:
        """索引 Markdown 文档"""
        file_path = self.document_manager.get_document_file_path(document.id)

        # 使用 PageIndex 索引 Markdown
        from pageindex.page_index_md import md_to_tree

        result = md_to_tree(
            md_path=str(file_path),
            if_thinning=False,
            min_token_threshold=5000,
            if_add_node_summary=self.settings.if_add_node_summary == "yes",
            summary_token_threshold=200,
            model=self.settings.deepseek_model,
            if_add_doc_description=self.settings.if_add_doc_description == "yes",
            if_add_node_text=self.settings.if_add_node_text == "yes",
            if_add_node_id=self.settings.if_add_node_id == "yes",
        )
        tree_data = asyncio.run(result) if asyncio.iscoroutine(result) else result
        return tree_data

    def _save_tree_data(self, doc_id: int, tree_data: dict):
        """保存树状数据到数据库"""
        # 清除旧索引
        self.session.query(PageIndex).filter(PageIndex.document_id == doc_id).delete()

        # 兼容 PageIndex 返回结构：dict{structure: [...]} / list / node dict
        if isinstance(tree_data, dict) and "structure" in tree_data:
            root_nodes = tree_data["structure"] or []
        elif isinstance(tree_data, list):
            root_nodes = tree_data
        else:
            root_nodes = [tree_data]

        # 递归保存节点
        for node in root_nodes:
            self._save_node_recursive(doc_id, node, parent_id=None)

        self.session.commit()

    def _save_node_recursive(self, doc_id: int, node_data: dict, parent_id: Optional[str]):
        """递归保存节点"""
        node = PageIndex(
            document_id=doc_id,
            node_id=node_data.get("node_id", ""),
            parent_id=parent_id,
            level=node_data.get("level", 0),
            title=node_data.get("title", ""),
            summary=node_data.get("summary"),
            page_start=node_data.get("page_start"),
            page_end=node_data.get("page_end"),
            content=node_data.get("content"),
            token_count=node_data.get("token_count"),
            node_metadata=json.dumps(node_data.get("metadata", {})),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.session.add(node)
        self.session.flush()  # 获取 node.id

        # 递归保存子节点
        children = node_data.get("children", [])
        for child_data in children:
            self._save_node_recursive(doc_id, child_data, parent_id=node.node_id)

