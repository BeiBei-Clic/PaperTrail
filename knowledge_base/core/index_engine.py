"""
Index engine for knowledge base system.
Integrates with PageIndex to generate and manage document indexes.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from sqlalchemy.orm import Session

# Add parent directory to path to import from pageindex
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pageindex.page_index import page_index_main
from pageindex.page_index_md import md_to_tree
from pageindex.utils import ConfigLoader

from knowledge_base.storage.models import Document, PageIndex
from knowledge_base.core.document_manager import DocumentManager
from knowledge_base.core.tree_search import TreeSearch
from knowledge_base.config.settings import get_settings

logger = logging.getLogger(__name__)


class IndexEngine:
    """
    Index engine for processing documents with PageIndex integration.
    """

    def __init__(self, session: Session):
        """
        Initialize index engine.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.settings = get_settings()
        self.document_manager = DocumentManager(session, FileStorage(self.settings.storage_path))

    def index_document(self, doc_id: int) -> Optional[PageIndex]:
        """
        Generate index for a document using PageIndex.

        Args:
            doc_id: Document ID

        Returns:
            Created PageIndex object, or None if failed
        """
        # Get document
        document = self.document_manager.get_document(doc_id)
        if not document:
            logger.error(f"Document not found: {doc_id}")
            return None

        # Update status to indexing
        self.document_manager.update_status(doc_id, "indexing")

        try:
            logger.info(f"Indexing document: {document.doc_name} (ID: {doc_id})")

            # Generate tree structure based on document type
            if document.doc_type == 'pdf':
                tree_data = self._index_pdf(document)
            elif document.doc_type == 'markdown':
                tree_data = self._index_markdown(document)
            else:
                raise ValueError(f"Unsupported document type: {document.doc_type}")

            # Extract metadata
            tree_structure = tree_data.get("structure", [])
            total_nodes = TreeSearch.count_nodes(tree_structure)
            max_depth = TreeSearch.get_max_depth(tree_structure)

            # Extract document description if generated
            doc_description = tree_data.get("doc_description")
            if doc_description and not document.doc_description:
                document.doc_description = doc_description

            # Update or create index record
            existing_index = self.document_manager.get_document_index(doc_id)

            if existing_index:
                # Update existing index
                existing_index.tree_structure = tree_structure
                existing_index.total_nodes = total_nodes
                existing_index.max_depth = max_depth
                page_index = existing_index
            else:
                # Create new index
                page_index = PageIndex(
                    document_id=doc_id,
                    tree_structure=tree_structure,
                    total_nodes=total_nodes,
                    max_depth=max_depth,
                )
                self.session.add(page_index)

            # Update document status
            self.document_manager.update_status(doc_id, "ready")

            self.session.commit()
            self.session.refresh(page_index)

            logger.info(f"Document indexed successfully: {document.doc_name} (nodes: {total_nodes}, depth: {max_depth})")
            return page_index

        except (ValueError, IOError, RuntimeError) as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            self.document_manager.update_status(doc_id, "error", str(e))
            self.session.rollback()
            raise

    def _index_pdf(self, document: Document) -> Dict[str, Any]:
        """
        Index a PDF document using PageIndex.

        Args:
            document: Document object

        Returns:
            Tree structure dictionary
        """
        # Load PageIndex configuration
        config_loader = ConfigLoader()
        opt = config_loader.load(self.settings.get_pageindex_config())

        # Generate tree structure
        logger.info(f"Processing PDF: {document.file_path}")
        tree_data = page_index_main(document.file_path, opt)

        # Update page count if available
        if tree_data and "structure" in tree_data:
            # Try to get page count from the tree structure
            page_indices = set()
            for node in TreeSearch.get_all_nodes(tree_data["structure"]):
                if "page_index" in node:
                    if isinstance(node["page_index"], list):
                        page_indices.update(node["page_index"])

            if page_indices:
                document.page_count = max(page_indices)

        return tree_data

    def _index_markdown(self, document: Document) -> Dict[str, Any]:
        """
        Index a Markdown document using PageIndex.

        Args:
            document: Document object

        Returns:
            Tree structure dictionary
        """
        # Load PageIndex configuration
        config_loader = ConfigLoader()
        opt = config_loader.load(self.settings.get_pageindex_config())

        # Generate tree structure
        logger.info(f"Processing Markdown: {document.file_path}")
        import asyncio
        tree_data = asyncio.run(md_to_tree(document.file_path, opt))

        return tree_data

    def reindex_document(self, doc_id: int) -> Optional[PageIndex]:
        """
        Re-index a document (delete existing index and create new one).

        Args:
            doc_id: Document ID

        Returns:
            Created PageIndex object, or None if failed
        """
        # Delete existing index
        existing_index = self.document_manager.get_document_index(doc_id)
        if existing_index:
            self.session.delete(existing_index)
            self.session.commit()

        # Create new index
        return self.index_document(doc_id)

    def delete_index(self, doc_id: int) -> bool:
        """
        Delete index for a document.

        Args:
            doc_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        existing_index = self.document_manager.get_document_index(doc_id)
        if existing_index:
            self.session.delete(existing_index)
            self.session.commit()
            logger.info(f"Index deleted for document: {doc_id}")
            return True
        return False

    def get_index_tree(self, doc_id: int) -> Optional[Dict]:
        """
        Get the tree structure for a document.

        Args:
            doc_id: Document ID

        Returns:
            Tree structure dictionary, or None if not found
        """
        page_index = self.document_manager.get_document_index(doc_id)
        if page_index:
            return page_index.tree_structure
        return None

    def validate_index(self, doc_id: int) -> bool:
        """
        Validate that an index is complete and valid.

        Args:
            doc_id: Document ID

        Returns:
            True if valid, False otherwise
        """
        page_index = self.document_manager.get_document_index(doc_id)
        if not page_index:
            return False

        # Check that tree structure exists and has nodes
        if not page_index.tree_structure or page_index.total_nodes == 0:
            return False

        # Check that the tree structure is valid JSON
        if not isinstance(page_index.tree_structure, list):
            return False

        # Validate that each node has required fields
        for node in TreeSearch.get_all_nodes(page_index.tree_structure):
            if not isinstance(node, dict):
                return False
            if "title" not in node:
                logger.warning(f"Node missing title in document {doc_id}")
                return False

        return True

    def batch_index(
        self,
        doc_ids: list,
        max_concurrent: int = None
    ) -> Dict[str, Any]:
        """
        Index multiple documents in batch.

        Args:
            doc_ids: List of document IDs to index
            max_concurrent: Maximum concurrent indexing tasks

        Returns:
            Dictionary with results
        """
        if max_concurrent is None:
            max_concurrent = self.settings.max_concurrent_indexing

        results = {
            "successful": [],
            "failed": [],
            "total": len(doc_ids),
        }

        # For now, process sequentially (can be enhanced with async processing)
        for doc_id in doc_ids:
            try:
                page_index = self.index_document(doc_id)
                if page_index:
                    results["successful"].append(doc_id)
                else:
                    results["failed"].append(doc_id)
            except Exception as e:
                logger.error(f"Failed to index document {doc_id}: {e}")
                results["failed"].append(doc_id)

        logger.info(f"Batch indexing complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
        return results
