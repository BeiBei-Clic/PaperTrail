"""
Document manager for knowledge base system.
Handles document upload, deletion, update, and status management.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from knowledge_base.storage.models import Document, PageIndex
from knowledge_base.storage.file_storage import FileStorage
from knowledge_base.config.settings import get_settings

logger = logging.getLogger(__name__)


class DocumentManager:
    """
    Manages document lifecycle in the knowledge base.
    """

    def __init__(self, session: Session, file_storage: FileStorage):
        """
        Initialize document manager.

        Args:
            session: SQLAlchemy database session
            file_storage: FileStorage instance
        """
        self.session = session
        self.file_storage = file_storage

    def add_document(
        self,
        file_path: str,
        doc_type: str,
        doc_name: str = None,
        description: str = None
    ) -> Document:
        """
        Add a new document to the knowledge base.

        Args:
            file_path: Path to the document file
            doc_type: Type of document ('pdf' or 'markdown')
            doc_name: Optional custom document name (defaults to filename)
            description: Optional document description

        Returns:
            Created Document object

        Raises:
            ValueError: If file doesn't exist or document type is invalid
            FileExistsError: If document with same name already exists
        """
        # Validate file
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        # Determine document name
        if doc_name is None:
            doc_name = Path(file_path).name

        # Check if document already exists
        existing = self.session.query(Document).filter_by(doc_name=doc_name).first()
        if existing:
            raise FileExistsError(f"Document with name '{doc_name}' already exists")

        # Validate document type
        if doc_type not in ['pdf', 'markdown']:
            raise ValueError(f"Invalid document type: {doc_type}. Must be 'pdf' or 'markdown'")

        # Get file size
        file_size = os.path.getsize(file_path)

        # Save file to storage
        stored_path = self.file_storage.save_file(file_path, doc_name)

        # Create document record
        document = Document(
            doc_name=doc_name,
            doc_type=doc_type,
            file_path=str(stored_path),
            file_size=file_size,
            page_count=0,
            doc_description=description,
            status="pending"
        )

        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)

        return document

    def delete_document(self, doc_id: int) -> bool:
        """
        Delete a document from the knowledge base.

        Args:
            doc_id: Document ID

        Returns:
            True if document was deleted, False if not found
        """
        document = self.session.query(Document).filter_by(id=doc_id).first()

        if not document:
            return False

        # Delete file from storage
        self.file_storage.delete_file(document.doc_name)

        # Delete database record (cascade will delete indexes)
        self.session.delete(document)
        self.session.commit()

        return True

    def update_document(
        self,
        doc_id: int,
        new_file_path: str = None,
        description: str = None
    ) -> Optional[Document]:
        """
        Update an existing document.

        Args:
            doc_id: Document ID
            new_file_path: Optional new file path to replace the document
            description: Optional new description

        Returns:
            Updated Document object, or None if not found
        """
        document = self.session.query(Document).filter_by(id=doc_id).first()

        if not document:
            return None

        # Update file if provided
        if new_file_path:
            if not os.path.exists(new_file_path):
                raise ValueError(f"File not found: {new_file_path}")

            # Delete old file
            self.file_storage.delete_file(document.doc_name)

            # Save new file
            stored_path = self.file_storage.save_file(new_file_path, document.doc_name)
            document.file_path = str(stored_path)
            document.file_size = os.path.getsize(new_file_path)
            document.status = "pending"  # Needs re-indexing
            document.indexed_at = None

        # Update description if provided
        if description is not None:
            document.doc_description = description

        document.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(document)

        return document

    def get_document(self, doc_id: int) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document object, or None if not found
        """
        return self.session.query(Document).filter_by(id=doc_id).first()

    def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str = None,
        doc_type: str = None
    ) -> List[Document]:
        """
        List documents with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            doc_type: Optional document type filter

        Returns:
            List of Document objects
        """
        query = self.session.query(Document)

        if status:
            query = query.filter_by(status=status)

        if doc_type:
            query = query.filter_by(doc_type=doc_type)

        return query.offset(skip).limit(limit).all()

    def update_status(
        self,
        doc_id: int,
        status: str,
        error_message: str = None
    ) -> Optional[Document]:
        """
        Update document status.

        Args:
            doc_id: Document ID
            status: New status ('pending', 'indexing', 'ready', 'error')
            error_message: Optional error message (for status='error')

        Returns:
            Updated Document object, or None if not found
        """
        document = self.session.query(Document).filter_by(id=doc_id).first()

        if not document:
            return None

        document.status = status
        document.error_message = error_message

        if status == "ready":
            document.indexed_at = datetime.utcnow()

        document.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(document)

        return document

    def get_document_index(self, doc_id: int) -> Optional[PageIndex]:
        """
        Get the index for a document.

        Args:
            doc_id: Document ID

        Returns:
            PageIndex object, or None if not found
        """
        return self.session.query(PageIndex).filter_by(document_id=doc_id).first()

    def get_documents_by_status(self, status: str) -> List[Document]:
        """
        Get all documents with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of Document objects
        """
        return self.session.query(Document).filter_by(status=status).all()

    def count_documents(self, status: str = None, doc_type: str = None) -> int:
        """
        Count documents with optional status filter.

        Args:
            status: Optional status filter
            doc_type: Optional document type filter

        Returns:
            Number of documents
        """
        query = self.session.query(Document)

        if status:
            query = query.filter_by(status=status)

        if doc_type:
            query = query.filter_by(doc_type=doc_type)

        return query.count()

    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        total_docs = self.count_documents()
        docs_by_status = {}
        docs_by_type = {}

        for status in ['pending', 'indexing', 'ready', 'error']:
            docs_by_status[status] = self.count_documents(status)

        for doc_type in ['pdf', 'markdown']:
            docs_by_type[doc_type] = self.count_documents(None, doc_type)

        total_storage_size = self.file_storage.get_storage_size()

        return {
            "total_documents": total_docs,
            "by_status": docs_by_status,
            "by_type": docs_by_type,
            "total_storage_bytes": total_storage_size,
            "total_storage_mb": round(total_storage_size / (1024 * 1024), 2),
        }
