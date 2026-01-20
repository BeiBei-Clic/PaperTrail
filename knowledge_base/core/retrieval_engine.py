"""
Retrieval engine for knowledge base system.
Implements tree search and LLM-based retrieval.
"""

import sys
import os
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directory to path to import from pageindex
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pageindex.utils import ChatGPT_API, ChatGPT_API_async, count_tokens

from knowledge_base.storage.models import Document, PageIndex
from knowledge_base.core.document_manager import DocumentManager
from knowledge_base.core.tree_search import TreeSearch
from knowledge_base.config.settings import get_settings

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """
    Retrieval engine for searching indexed documents using LLM reasoning.
    """

    def __init__(self, session: Session):
        """
        Initialize retrieval engine.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.settings = get_settings()
        self.document_manager = DocumentManager(session, FileStorage(self.settings.storage_path))

    def search(
        self,
        query: str,
        doc_ids: List[int] = None,
        top_k: int = None,
        with_answer: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a search query across documents.

        Args:
            query: Search query text
            doc_ids: Optional list of document IDs to search (default: all)
            top_k: Number of results to return (default: from settings)
            with_answer: Whether to generate an LLM answer

        Returns:
            Dictionary with search results
        """
        start_time = datetime.now()

        if top_k is None:
            top_k = self.settings.default_top_k

        logger.info(f"Executing search: query='{query}', doc_ids={doc_ids}, top_k={top_k}")

        # Get documents to search
        if doc_ids is None:
            # Search all indexed documents
            documents = self.session.query(Document).filter_by(status="ready").all()
        else:
            documents = [self.document_manager.get_document(doc_id) for doc_id in doc_ids]
            documents = [doc for doc in documents if doc and doc.status == "ready"]

        if not documents:
            logger.warning("No documents available for search")
            return {
                "query": query,
                "results": [],
                "answer": None,
                "latency_ms": 0,
            }

        # Collect tree structures
        trees = []
        for doc in documents:
            page_index = self.document_manager.get_document_index(doc.id)
            if page_index and page_index.tree_structure:
                trees.append({
                    "document": doc,
                    "tree": page_index.tree_structure,
                })

        if not trees:
            logger.warning("No valid tree structures found for search")
            return {
                "query": query,
                "results": [],
                "answer": None,
                "latency_ms": 0,
            }

        # Perform tree search with LLM reasoning
        relevant_nodes = self._tree_search_with_llm(query, trees, top_k)

        # Extract results
        results = []
        for node_info in relevant_nodes:
            doc = node_info["document"]
            node = node_info["node"]

            result = {
                "document_id": doc.id,
                "doc_name": doc.doc_name,
                "doc_type": doc.doc_type,
                "node": {
                    "node_id": node.get("node_id"),
                    "title": node.get("title"),
                    "summary": node.get("summary"),
                    "page_index": node.get("page_index"),
                    "line_num": node.get("line_num"),
                },
                "content": node.get("text", ""),
                "score": node_info.get("score", 0.0),
            }
            results.append(result)

        # Generate answer if requested
        answer = None
        if with_answer and results:
            answer = self._generate_answer(query, results)

        # Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"Search completed: {len(results)} results, {latency_ms:.2f}ms")

        return {
            "query": query,
            "results": results,
            "answer": answer,
            "latency_ms": round(latency_ms, 2),
        }

    def _tree_search_with_llm(
        self,
        query: str,
        trees: List[Dict],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Perform tree search with LLM reasoning.

        Args:
            query: Search query
            trees: List of tree structures with documents
            top_k: Number of results to return

        Returns:
            List of relevant nodes with documents
        """
        # Build a prompt for LLM to reason about the tree structure
        all_nodes = []

        for tree_info in trees:
            doc = tree_info["document"]
            tree = tree_info["tree"]

            # Get all nodes from tree
            for node in TreeSearch.get_all_nodes(tree):
                all_nodes.append({
                    "document": doc,
                    "node": node,
                })

        # If we have summaries, use them for efficient search
        # Otherwise, use titles
        summaries_list = []
        for node_info in all_nodes:
            node = node_info["node"]
            summary = node.get("summary") or node.get("title", "")
            node_id = node.get("node_id", "unknown")

            summaries_list.append(f"Node {node_id}: {summary}")

        # Create LLM prompt for node selection
        system_prompt = """You are a search assistant that helps users find relevant information in documents.
You will be given a list of document sections (nodes) with their summaries or titles.
Select the most relevant nodes for the user's query.

Return your response as a JSON object with this format:
{
    "selected_nodes": ["node_id_1", "node_id_2", ...],
    "reasoning": "Brief explanation of why these nodes are relevant"
}

Select up to {max_nodes} nodes. If fewer nodes are relevant, select fewer."""

        user_prompt = f"""Query: {query}

Available document sections:
{chr(10).join(summaries_list[:50])}  # Limit to first 50 nodes to avoid token limit

Which nodes are most relevant to the query?"""

        # Call LLM
        response = ChatGPT_API(
            messages=[
                {"role": "system", "content": system_prompt.format(max_nodes=top_k)},
                {"role": "user", "content": user_prompt}
            ],
            model=self.settings.openai_model,
            temperature=self.settings.search_temperature,
        )

        # Parse response
        response_json = extract_json_from_response(response)

        if response_json and "selected_nodes" in response_json:
            selected_node_ids = response_json["selected_nodes"]
            reasoning = response_json.get("reasoning", "")

            logger.info(f"LLM selected nodes: {selected_node_ids}, reasoning: {reasoning}")

            # Find selected nodes
            selected_nodes = []
            for node_info in all_nodes:
                node_id = node_info["node"].get("node_id")
                if node_id in selected_node_ids:
                    # Use selection order as relevance score
                    order = selected_node_ids.index(node_id)
                    score = 1.0 - (order / len(selected_node_ids))
                    node_info["score"] = score
                    selected_nodes.append(node_info)

            return selected_nodes[:top_k]

        # No valid nodes selected: keyword-based search
        logger.info("No nodes selected by LLM, falling back to keyword-based search")
        return self._keyword_search(query, all_nodes, top_k)

    def _keyword_search(
        self,
        query: str,
        all_nodes: List[Dict],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback keyword-based search.

        Args:
            query: Search query
            all_nodes: List of all nodes with documents
            top_k: Number of results to return

        Returns:
            List of relevant nodes with documents
        """
        query_lower = query.lower()
        scored_nodes = []

        for node_info in all_nodes:
            node = node_info["node"]
            score = 0.0

            # Check title
            title = node.get("title", "").lower()
            if query_lower in title:
                score += 0.5

            # Check summary
            summary = node.get("summary", "").lower()
            if query_lower in summary:
                score += 0.3

            # Check text
            text = node.get("text", "").lower()
            if query_lower in text:
                score += 0.2

            if score > 0:
                node_info["score"] = score
                scored_nodes.append(node_info)

        # Sort by score and return top_k
        scored_nodes.sort(key=lambda x: x.get("score", 0), reverse=True)
        return scored_nodes[:top_k]

    def _generate_answer(self, query: str, results: List[Dict]) -> str:
        """
        Generate an answer based on search results using LLM.

        Args:
            query: Original search query
            results: Search results with content

        Returns:
            Generated answer
        """
        # Build context from results
        context_parts = []
        total_tokens = 0
        max_tokens = self.settings.max_context_tokens

        for result in results:
            doc_name = result["doc_name"]
            title = result["node"]["title"]
            content = result["content"]

            context_part = f"[Document: {doc_name}, Section: {title}]\n{content}\n"
            tokens = count_tokens(context_part)

            if total_tokens + tokens > max_tokens:
                # Truncate content to fit
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 100:  # Only add if we have space
                    # Rough approximation: 1 token ≈ 0.75 words
                    max_chars = int(remaining_tokens * 3)
                    content = content[:max_chars] + "..."
                    context_part = f"[Document: {doc_name}, Section: {title}]\n{content}\n"
                    context_parts.append(context_part)
                break

            context_parts.append(context_part)
            total_tokens += tokens

        context = "\n".join(context_parts)

        # Generate answer
        system_prompt = """You are a helpful assistant that answers questions based on provided document excerpts.
Use only the information from the provided context to answer the question.
If the context doesn't contain enough information to answer the question, say so.
Be concise and accurate in your response."""

        user_prompt = f"""Question: {query}

Context:
{context}

Please answer the question based on the context above."""

        response = ChatGPT_API(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.settings.openai_model,
            temperature=0.3,
        )

        return response.strip()

    def retrieve_content(self, doc_id: int, node_id: str) -> Optional[str]:
        """
        Retrieve full content of a specific node.

        Args:
            doc_id: Document ID
            node_id: Node ID

        Returns:
            Node content text, or None if not found
        """
        page_index = self.document_manager.get_document_index(doc_id)
        if not page_index:
            return None

        node = TreeSearch.find_node_by_id(page_index.tree_structure, node_id)
        if node:
            return node.get("text", "")

        return None


def extract_json_from_response(response: str) -> Optional[Dict]:
    """
    Extract JSON from LLM response.

    Args:
        response: LLM response string

    Returns:
        Parsed JSON dictionary, or None if parsing fails
    """
    try:
        # Try to parse directly
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        try:
            # Find JSON object in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to extract JSON from response: {e}")

    return None
