"""Pydantic 数据验证模型"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# 文档相关模型
class DocumentBase(BaseModel):
    """文档基础模型"""
    filename: str
    original_filename: str
    doc_type: str
    title: Optional[str] = None
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    """创建文档模型"""
    file_content: bytes = Field(..., description="文件内容")


class DocumentResponse(DocumentBase):
    """文档响应模型"""
    id: int
    file_path: str
    file_size: int
    status: str
    indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int
    documents: List[DocumentResponse]


# 索引相关模型
class IndexRequest(BaseModel):
    """索引请求模型"""
    document_id: int


class IndexResponse(BaseModel):
    """索引响应模型"""
    document_id: int
    status: str
    message: str


# 搜索相关模型
class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., min_length=1, description="搜索查询")
    doc_ids: Optional[List[int]] = Field(None, description="要搜索的文档ID列表")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")
    search_type: str = Field("agent", description="搜索类型：agent 或 simple")


class SearchResult(BaseModel):
    """搜索结果模型"""
    node_id: str
    title: str
    summary: Optional[str] = None
    document_id: int
    level: int
    relevance_score: float = 0.0


class SearchResponse(BaseModel):
    """搜索响应模型"""
    query: str
    results: List[SearchResult]
    total: int
    answer: Optional[str] = None
    intermediate_steps: Optional[List[dict]] = None


# 节点相关模型
class NodeResponse(BaseModel):
    """节点响应模型"""
    node_id: str
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    level: int
    document_id: int


class NodePathResponse(BaseModel):
    """节点路径响应模型"""
    node_id: str
    title: str
    level: int


# 通用响应模型
class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    detail: Optional[str] = None


class MessageResponse(BaseModel):
    """消息响应模型"""
    message: str
    success: bool = True
