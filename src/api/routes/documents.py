"""文档管理接口"""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.api.schemas import (
    DocumentListResponse,
    DocumentResponse,
    IndexResponse,
    MessageResponse,
)
from src.config.settings import get_settings
from src.core.document_manager import DocumentManager
from src.core.index_engine import IndexEngine
from src.storage.database import get_session
from src.storage.file_storage import FileStorage

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_manager():
    """获取文档管理器依赖"""
    from src.storage.database import get_session

    session = next(get_session())
    return DocumentManager(session)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "auto",
    title: str = None,
    description: str = None,
):
    """
    上传文档

    支持的文件类型：
    - PDF: .pdf
    - Markdown: .md, .markdown
    - Text: .txt
    """
    settings = get_settings()
    file_storage = FileStorage()

    # 读取文件内容
    file_content = await file.read()

    # 验证文件大小
    if not file_storage.validate_file_size(file_content):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制 ({settings.max_file_size} bytes)",
        )

    # 自动检测文档类型
    if doc_type == "auto":
        if file.filename.endswith(".pdf"):
            doc_type = "pdf"
        elif file.filename.endswith((".md", ".markdown")):
            doc_type = "markdown"
        elif file.filename.endswith(".txt"):
            doc_type = "txt"
        else:
            doc_type = "unknown"

    # 保存文件
    filename = file_storage.save_file(file_content, file.filename)

    # 创建文档记录
    with get_session() as session:
        document_manager = DocumentManager(session)
        document = document_manager.create_document(
            filename=filename,
            original_filename=file.filename,
            file_path=str(file_storage.get_file_path(filename)),
            file_size=len(file_content),
            doc_type=doc_type,
            title=title,
            description=description,
        )
        session.commit()

    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
):
    """
    获取文档列表

    参数：
    - skip: 跳过的记录数
    - limit: 返回的记录数
    - status_filter: 状态过滤（pending, indexing, indexed, failed）
    """
    with get_session() as session:
        document_manager = DocumentManager(session)
        documents = document_manager.get_all_documents(skip, limit, status_filter)
        total = document_manager.count_documents(status_filter)

    return DocumentListResponse(
        total=total,
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int):
    """获取文档详情"""
    with get_session() as session:
        document_manager = DocumentManager(session)
        document = document_manager.get_document(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {document_id}",
        )

    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(document_id: int):
    """删除文档"""
    with get_session() as session:
        document_manager = DocumentManager(session)
        success = document_manager.delete_document(document_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {document_id}",
        )

    return MessageResponse(message="文档删除成功")


@router.post("/{document_id}/index", response_model=IndexResponse)
def index_document(document_id: int):
    """
    索引文档

    启动文档的索引流程，生成树状结构。
    """
    with get_session() as session:
        document_manager = DocumentManager(session)
        document = document_manager.get_document(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {document_id}",
        )

    try:
        index_engine = IndexEngine(session)
        indexed_document = index_engine.index_document(document_id)

        return IndexResponse(
            document_id=document_id,
            status=indexed_document.status,
            message="索引完成",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"索引失败: {str(e)}",
        )


@router.get("/{document_id}/status", response_model=DocumentResponse)
def get_document_status(document_id: int):
    """获取文档索引状态"""
    with get_session() as session:
        document_manager = DocumentManager(session)
        document = document_manager.get_document(document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {document_id}",
        )

    return DocumentResponse.model_validate(document)
