"""
Document management API routes.
"""

import os
import tempfile
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from knowledge_base.storage.database import get_db
from knowledge_base.storage.models import Document
from knowledge_base.storage.file_storage import FileStorage
from knowledge_base.core.document_manager import DocumentManager
from knowledge_base.core.index_engine import IndexEngine
from knowledge_base.api.schemas import (
    DocumentResponse,
    DocumentListResponse,
    StatusResponse,
    StorageStatsResponse,
    BatchIndexRequest,
    BatchIndexResponse,
)
from knowledge_base.config.settings import get_settings

router = APIRouter(prefix="/api/documents", tags=["documents"])
settings = get_settings()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Query(..., description="Document type: 'pdf' or 'markdown'"),
    description: str = Query(None, description="Document description"),
    db: Session = Depends(get_db)
):
    """
    Upload a new document to the knowledge base.

    - **file**: Document file (PDF or Markdown)
    - **doc_type**: Type of document ('pdf' or 'markdown')
    - **description**: Optional document description
    """
    # Validate file extension matches document type
    filename = file.filename
    if doc_type == 'pdf' and not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    if doc_type == 'markdown' and not (filename.lower().endswith('.md') or filename.lower().endswith('.markdown')):
        raise HTTPException(status_code=400, detail="File must be a Markdown file")

    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
        )

    # Save file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name

    try:
        # Create document in database
        file_storage = FileStorage(settings.storage_path)
        doc_manager = DocumentManager(db, file_storage)
        document = doc_manager.add_document(
            file_path=tmp_file_path,
            doc_type=doc_type,
            doc_name=filename,
            description=description
        )

        return DocumentResponse(**document.to_dict())

    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Get a document by ID.

    - **doc_id**: Document ID
    """
    file_storage = FileStorage(settings.storage_path)
    doc_manager = DocumentManager(db, file_storage)
    document = doc_manager.get_document(doc_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    return DocumentResponse(**document.to_dict())


@router.delete("/{doc_id}", response_model=StatusResponse)
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Delete a document by ID.

    - **doc_id**: Document ID
    """
    file_storage = FileStorage(settings.storage_path)
    doc_manager = DocumentManager(db, file_storage)
    success = doc_manager.delete_document(doc_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    return StatusResponse(
        status="success",
        message=f"Document deleted: {doc_id}"
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: str = Query(None, description="Filter by status"),
    doc_type: str = Query(None, description="Filter by document type"),
    db: Session = Depends(get_db)
):
    """
    List documents with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Optional status filter ('pending', 'indexing', 'ready', 'error')
    - **doc_type**: Optional document type filter ('pdf', 'markdown')
    """
    file_storage = FileStorage(settings.storage_path)
    doc_manager = DocumentManager(db, file_storage)
    documents = doc_manager.list_documents(skip=skip, limit=limit, status=status, doc_type=doc_type)

    total = doc_manager.count_documents(status=status, doc_type=doc_type)

    return DocumentListResponse(
        total=total,
        documents=[DocumentResponse(**doc.to_dict()) for doc in documents]
    )


@router.get("/{doc_id}/status", response_model=StatusResponse)
def get_document_status(doc_id: int, db: Session = Depends(get_db)):
    """
    Get the indexing status of a document.

    - **doc_id**: Document ID
    """
    file_storage = FileStorage(settings.storage_path)
    doc_manager = DocumentManager(db, file_storage)
    document = doc_manager.get_document(doc_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    index_engine = IndexEngine(db)
    is_valid = index_engine.validate_index(doc_id)

    return StatusResponse(
        status=document.status,
        message=f"Document status: {document.status}",
        data={
            "doc_id": document.id,
            "doc_name": document.doc_name,
            "status": document.status,
            "indexed": document.status == "ready",
            "index_valid": is_valid,
            "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None,
            "error_message": document.error_message,
        }
    )


@router.post("/{doc_id}/index", response_model=StatusResponse)
def index_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Trigger indexing for a document.

    - **doc_id**: Document ID
    """
    file_storage = FileStorage(settings.storage_path)
    doc_manager = DocumentManager(db, file_storage)
    document = doc_manager.get_document(doc_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    index_engine = IndexEngine(db)
    page_index = index_engine.index_document(doc_id)

    if not page_index:
        raise HTTPException(status_code=500, detail="Failed to index document")

    return StatusResponse(
        status="success",
        message=f"Document indexed successfully: {doc_id}",
        data={
            "doc_id": doc_id,
            "total_nodes": page_index.total_nodes,
            "max_depth": page_index.max_depth,
        }
    )


@router.post("/{doc_id}/reindex", response_model=StatusResponse)
def reindex_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Re-index a document (delete existing index and create new one).

    - **doc_id**: Document ID
    """
    file_storage = FileStorage(settings.storage_path)
    doc_manager = DocumentManager(db, file_storage)
    document = doc_manager.get_document(doc_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    index_engine = IndexEngine(db)
    page_index = index_engine.reindex_document(doc_id)

    if not page_index:
        raise HTTPException(status_code=500, detail="Failed to re-index document")

    return StatusResponse(
        status="success",
        message=f"Document re-indexed successfully: {doc_id}",
        data={
            "doc_id": doc_id,
            "total_nodes": page_index.total_nodes,
            "max_depth": page_index.max_depth,
        }
    )


@router.get("/stats/storage", response_model=StorageStatsResponse)
def get_storage_stats(db: Session = Depends(get_db)):
    """
    Get storage statistics.

    Returns information about documents and storage usage.
    """
    file_storage = FileStorage(settings.storage_path)
    doc_manager = DocumentManager(db, file_storage)
    stats = doc_manager.get_storage_stats()

    return StorageStatsResponse(**stats)


@router.post("/batch/index", response_model=BatchIndexResponse)
def batch_index_documents(
    request: BatchIndexRequest,
    db: Session = Depends(get_db)
):
    """
    Index multiple documents in batch.

    - **doc_ids**: List of document IDs to index
    - **max_concurrent**: Maximum concurrent indexing tasks (optional)
    """
    index_engine = IndexEngine(db)
    results = index_engine.batch_index(
        doc_ids=request.doc_ids,
        max_concurrent=request.max_concurrent
    )

    return BatchIndexResponse(**results)
