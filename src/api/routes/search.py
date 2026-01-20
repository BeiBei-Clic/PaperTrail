"""搜索接口"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.agents.retrieval_agent import RetrievalAgent
from src.api.schemas import (
    NodeResponse,
    NodePathResponse,
    SearchRequest,
    SearchResponse,
)
from src.core.retrieval_engine import RetrievalEngine
from src.storage.database import get_session

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """
    执行智能搜索（使用 Agent）

    Agent 会自动选择合适的工具进行搜索和内容提取。
    """
    with get_session() as session:
        agent = RetrievalAgent(session)

        try:
            start_time = time.time()
            result = agent.search(request.query, request.top_k)
            execution_time = time.time() - start_time

            # 如果没有返回结果，返回空响应
            if "results" not in result:
                result["results"] = []

            return SearchResponse(**result)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"搜索失败: {str(e)}",
            )


@router.post("/simple", response_model=SearchResponse)
def simple_search(request: SearchRequest):
    """
    执行简单搜索（不使用 Agent）

    直接使用关键词或语义搜索，不经过 Agent 推理。
    """
    with get_session() as session:
        retrieval_engine = RetrievalEngine(session)

        try:
            # 使用语义搜索
            result = retrieval_engine.semantic_search(
                request.query, request.doc_ids, request.top_k
            )

            return SearchResponse(**result)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"搜索失败: {str(e)}",
            )


@router.get("/node/{node_id}", response_model=NodeResponse)
def get_node(node_id: str):
    """获取节点完整内容"""
    with get_session() as session:
        retrieval_engine = RetrievalEngine(session)
        node_data = retrieval_engine.get_node_content(node_id)

    if not node_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点不存在: {node_id}",
        )

    return NodeResponse(**node_data)


@router.get("/node/{node_id}/path", response_model=list[NodePathResponse])
def get_node_path(node_id: str):
    """获取从根节点到指定节点的路径"""
    from src.core.tree_search import TreeSearchEngine

    with get_session() as session:
        engine = TreeSearchEngine(session)
        path = engine.get_node_path(node_id)

    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点不存在: {node_id}",
        )

    return [NodePathResponse(**{"node_id": n.node_id, "title": n.title, "level": n.level}) for n in path]


@router.get("/document/{document_id}/structure")
def get_document_structure(document_id: int):
    """获取文档的树状结构"""
    with get_session() as session:
        retrieval_engine = RetrievalEngine(session)
        structure = retrieval_engine.get_document_structure(document_id)

    return structure
