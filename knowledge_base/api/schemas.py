"""
Pydantic schemas for API request/response validation.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Document Schemas
# ============================================================================

class DocumentBase(BaseModel):
    """Base document schema."""
    doc_name: str = Field(..., description="Document name")
    doc_type: Literal['pdf', 'markdown'] = Field(..., description="Document type: 'pdf' or 'markdown'")
    description: Optional[str] = Field(None, description="Document description")


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    file_path: str = Field(..., description="Path to the document file")


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    new_file_path: Optional[str] = Field(None, description="New file path")
    description: Optional[str] = Field(None, description="New description")


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: int
    doc_name: str
    doc_type: Literal['pdf', 'markdown']
    file_path: str
    file_size: int
    page_count: int
    doc_description: Optional[str]
    status: Literal['pending', 'indexing', 'ready', 'error']
    error_message: Optional[str]
    indexed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    total: int
    documents: List[DocumentResponse]


# ============================================================================
# PageIndex Schemas
# ============================================================================

class PageIndexResponse(BaseModel):
    """Schema for page index response."""
    id: int
    document_id: int
    total_nodes: int
    max_depth: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TreeNodeResponse(BaseModel):
    """Schema for tree node response."""
    node_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    page_index: Optional[List[int]] = None
    line_num: Optional[int] = None


# ============================================================================
# Search Schemas
# ============================================================================

class SearchRequest(BaseModel):
    """Schema for search request."""
    query: str = Field(..., min_length=1, description="Search query text")
    doc_ids: Optional[List[int]] = Field(None, description="List of document IDs to search")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of results to return")
    with_answer: Optional[bool] = Field(True, description="Whether to generate an answer")


class SearchResultNode(BaseModel):
    """Schema for search result node."""
    node_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    page_index: Optional[List[int]] = None
    line_num: Optional[int] = None


class SearchResult(BaseModel):
    """Schema for single search result."""
    document_id: int
    doc_name: str
    doc_type: str
    node: SearchResultNode
    content: str
    score: float = Field(..., ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    """Schema for search response."""
    query: str
    results: List[SearchResult]
    answer: Optional[str] = None
    latency_ms: float


# ============================================================================
# Status Schemas
# ============================================================================

class StatusResponse(BaseModel):
    """Schema for status response."""
    status: Literal['success', 'error', 'pending', 'indexing', 'ready']
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: Literal['healthy', 'unhealthy', 'degraded']
    version: str
    configured: bool


# ============================================================================
# Statistics Schemas
# ============================================================================

class StorageStatsResponse(BaseModel):
    """Schema for storage statistics response."""
    total_documents: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    total_storage_bytes: int
    total_storage_mb: float


class TreeStatsResponse(BaseModel):
    """Schema for tree statistics response."""
    document_id: int
    doc_name: str
    total_nodes: int
    max_depth: int
    root_nodes: int
    leaf_nodes: int
    nodes_by_depth: Dict[int, int]
    avg_nodes_per_level: float


# ============================================================================
# Batch Operations Schemas
# ============================================================================

class BatchIndexRequest(BaseModel):
    """Schema for batch index request."""
    doc_ids: List[int] = Field(..., min_length=1, description="List of document IDs to index")
    max_concurrent: Optional[int] = Field(None, ge=1, le=10, description="Max concurrent indexing tasks")


class BatchIndexResponse(BaseModel):
    """Schema for batch index response."""
    total: int
    successful: List[int]
    failed: List[int]


# ============================================================================
# Validation
# ============================================================================
# Note: Document types and statuses are now validated using Literal types
# in the respective schema definitions above
