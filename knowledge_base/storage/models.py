"""
Data models for the knowledge base system.
Defines SQLAlchemy ORM models for documents and indexes.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Document(Base):
    """
    Document model representing uploaded documents.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_name = Column(String(255), unique=True, index=True, nullable=False)
    doc_type = Column(String(50), nullable=False)  # 'pdf' or 'markdown'
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    page_count = Column(Integer, default=0)  # For PDFs
    doc_description = Column(Text, nullable=True)  # AI-generated or user-provided
    status = Column(String(50), default="pending", nullable=False)  # pending, indexing, ready, error
    error_message = Column(Text, nullable=True)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship with indexes
    indexes = relationship("PageIndex", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "doc_name": self.doc_name,
            "doc_type": self.doc_type,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "doc_description": self.doc_description,
            "status": self.status,
            "error_message": self.error_message,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Document(id={self.id}, doc_name='{self.doc_name}', status='{self.status}')>"


class PageIndex(Base):
    """
    PageIndex model storing the tree structure for documents.
    """
    __tablename__ = "page_indexes"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tree_structure = Column(JSON, nullable=False)  # Full tree structure as JSON
    total_nodes = Column(Integer, default=0)  # Total number of nodes in the tree
    max_depth = Column(Integer, default=0)  # Maximum depth of the tree
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship with document
    document = relationship("Document", back_populates="indexes")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "tree_structure": self.tree_structure,
            "total_nodes": self.total_nodes,
            "max_depth": self.max_depth,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<PageIndex(id={self.id}, document_id={self.document_id}, total_nodes={self.total_nodes})>"


class SearchHistory(Base):
    """
    Search history model for tracking queries and results.
    """
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    doc_ids = Column(JSON, nullable=True)  # List of document IDs searched
    results_count = Column(Integer, default=0)  # Number of results returned
    with_answer = Column(Integer, default=0)  # Whether answer was generated (1=yes, 0=no)
    latency_ms = Column(Float, nullable=True)  # Query latency in milliseconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "query": self.query,
            "doc_ids": self.doc_ids,
            "results_count": self.results_count,
            "with_answer": bool(self.with_answer),
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<SearchHistory(id={self.id}, query='{self.query[:50]}...', results_count={self.results_count})>"
