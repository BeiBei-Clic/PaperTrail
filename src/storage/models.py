"""SQLAlchemy 数据模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """声明式基类"""
    pass


class Document(Base):
    """文档模型"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    doc_type = Column(String(50), nullable=False)  # pdf, markdown, txt
    title = Column(String(500))
    description = Column(Text)
    status = Column(String(50), default="pending")  # pending, indexing, indexed, failed
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    page_indices = relationship("PageIndex", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class PageIndex(Base):
    """页索引模型（树状结构）"""

    __tablename__ = "page_indices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    node_id = Column(String(100), nullable=False, index=True)  # 树节点 ID
    parent_id = Column(String(100), nullable=True, index=True)  # 父节点 ID

    # 节点信息
    level = Column(Integer, nullable=False)  # 层级
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    page_start = Column(Integer)
    page_end = Column(Integer)

    # 内容信息
    content = Column(Text)  # 节点完整内容（可选）
    token_count = Column(Integer)

    # 元数据
    metadata = Column(Text)  # JSON 格式的额外信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    document = relationship("Document", back_populates="page_indices")

    # 唯一约束
    __table_args__ = (
        UniqueConstraint("document_id", "node_id", name="uq_document_node"),
    )

    def __repr__(self):
        return f"<PageIndex(id={self.id}, node_id={self.node_id}, title={self.title})>"


class SearchHistory(Base):
    """搜索历史模型"""

    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    results_count = Column(Integer, default=0)
    search_type = Column(String(50), default="agent")  # agent, simple
    execution_time = Column(Float)  # 执行时间（秒）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SearchHistory(id={self.id}, query={self.query[:50]}...)"


class IndexingJob(Base):
    """索引任务模型"""

    __tablename__ = "indexing_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 进度 0-100
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<IndexingJob(id={self.id}, document_id={self.document_id}, status={self.status})>"
