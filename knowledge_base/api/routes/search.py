"""
Search API routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from knowledge_base.storage.database import get_db
from knowledge_base.core.retrieval_engine import RetrievalEngine
from knowledge_base.api.schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a search query across indexed documents.

    - **query**: Search query text
    - **doc_ids**: Optional list of document IDs to search (default: all documents)
    - **top_k**: Number of results to return (default: 5, max: 20)
    - **with_answer**: Whether to generate an LLM answer (default: true)

    The search uses LLM reasoning to find the most relevant sections from documents
    and optionally generates an answer based on the retrieved content.
    """
    retrieval_engine = RetrievalEngine(db)

    try:
        results = retrieval_engine.search(
            query=request.query,
            doc_ids=request.doc_ids,
            top_k=request.top_k,
            with_answer=request.with_answer
        )

        return SearchResponse(**results)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
