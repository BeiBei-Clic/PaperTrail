"""文档管理器"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from src.config.settings import get_settings
from src.storage.file_storage import FileStorage
from src.storage.models import Document


class DocumentManager:
    """文档管理器"""

    def __init__(self, session: Session):
        self.session = session
        self.settings = get_settings()
        self.file_storage = FileStorage()

    def create_document(
        self,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        doc_type: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Document:
        """创建新文档记录"""
        document = Document(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            doc_type=doc_type,
            title=title,
            description=description,
            status="pending",
            created_at=datetime.utcnow(),
        )

        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)

        return document

    def get_document(self, doc_id: int) -> Optional[Document]:
        """获取文档"""
        return self.session.query(Document).filter(Document.id == doc_id).first()

    def get_all_documents(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Document]:
        """获取所有文档"""
        query = self.session.query(Document)

        if status:
            query = query.filter(Document.status == status)

        return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    def update_document_status(self, doc_id: int, status: str) -> Optional[Document]:
        """更新文档状态"""
        document = self.get_document(doc_id)
        if document:
            document.status = status
            if status == "indexed":
                document.indexed_at = datetime.utcnow()
            document.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(document)
        return document

    def update_document(self, doc_id: int, **kwargs) -> Optional[Document]:
        """更新文档信息"""
        document = self.get_document(doc_id)
        if document:
            for key, value in kwargs.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            document.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(document)
        return document

    def delete_document(self, doc_id: int) -> bool:
        """删除文档"""
        document = self.get_document(doc_id)
        if document:
            # 删除文件
            self.file_storage.delete_file(document.filename)

            # 删除数据库记录（级联删除相关索引）
            self.session.delete(document)
            self.session.commit()
            return True
        return False

    def get_document_by_filename(self, filename: str) -> Optional[Document]:
        """根据文件名获取文档"""
        return self.session.query(Document).filter(Document.filename == filename).first()

    def count_documents(self, status: Optional[str] = None) -> int:
        """统计文档数量"""
        query = self.session.query(Document)
        if status:
            query = query.filter(Document.status == status)
        return query.count()

    def get_pending_documents(self) -> List[Document]:
        """获取待索引的文档"""
        return self.session.query(Document).filter(Document.status == "pending").all()

    def get_document_file_path(self, doc_id: int) -> Optional[Path]:
        """获取文档文件的完整路径"""
        document = self.get_document(doc_id)
        if document:
            return self.file_storage.get_file_path(document.filename)
        return None
