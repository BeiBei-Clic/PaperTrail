"""
Python client SDK for PageIndex Knowledge Base API.
Provides a simple interface for interacting with the knowledge base.
"""

import requests
from typing import List, Dict, Optional, Any
from pathlib import Path


class KnowledgeBaseClient:
    """
    Client for PageIndex Knowledge Base API.
    """

    def __init__(self, base_url: str = "http://localhost:8000", api_prefix: str = "/api"):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the API server
            api_prefix: API prefix path
        """
        self.base_url = base_url.rstrip('/')
        self.api_prefix = api_prefix.rstrip('/')
        self.api_url = f"{self.base_url}{self.api_prefix}"

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON as dictionary

        Raises:
            requests.HTTPError: If the request fails
        """
        url = f"{self.api_url}{endpoint}"
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Health Check
    # ========================================================================

    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status.

        Returns:
            Health status dictionary
        """
        return self._request("GET", "/health")

    # ========================================================================
    # Document Management
    # ========================================================================

    def upload_document(
        self,
        file_path: str,
        doc_type: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a document to the knowledge base.

        Args:
            file_path: Path to the document file
            doc_type: Document type ('pdf' or 'markdown')
            description: Optional document description

        Returns:
            Uploaded document information
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        files = {
            'file': (file_path_obj.name, open(file_path_obj, 'rb'))
        }

        params = {
            'doc_type': doc_type
        }
        if description:
            params['description'] = description

        try:
            return self._request("POST", "/documents/upload", files=files, params=params)
        finally:
            files['file'][1].close()

    def get_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document information
        """
        return self._request("GET", f"/documents/{doc_id}")

    def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List documents with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            doc_type: Optional document type filter

        Returns:
            Dictionary with total count and list of documents
        """
        params = {'skip': skip, 'limit': limit}
        if status:
            params['status'] = status
        if doc_type:
            params['doc_type'] = doc_type

        return self._request("GET", "/documents", params=params)

    def delete_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Deletion status
        """
        return self._request("DELETE", f"/documents/{doc_id}")

    def get_document_status(self, doc_id: int) -> Dict[str, Any]:
        """
        Get the indexing status of a document.

        Args:
            doc_id: Document ID

        Returns:
            Document status information
        """
        return self._request("GET", f"/documents/{doc_id}/status")

    def index_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Trigger indexing for a document.

        Args:
            doc_id: Document ID

        Returns:
            Indexing status
        """
        return self._request("POST", f"/documents/{doc_id}/index")

    def reindex_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Re-index a document.

        Args:
            doc_id: Document ID

        Returns:
            Re-indexing status
        """
        return self._request("POST", f"/documents/{doc_id}/reindex")

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Storage statistics
        """
        return self._request("GET", "/documents/stats/storage")

    def batch_index_documents(
        self,
        doc_ids: List[int],
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Index multiple documents in batch.

        Args:
            doc_ids: List of document IDs to index
            max_concurrent: Maximum concurrent indexing tasks

        Returns:
            Batch indexing results
        """
        data = {'doc_ids': doc_ids}
        if max_concurrent:
            data['max_concurrent'] = max_concurrent

        return self._request("POST", "/documents/batch/index", json=data)

    # ========================================================================
    # Search
    # ========================================================================

    def search(
        self,
        query: str,
        doc_ids: Optional[List[int]] = None,
        top_k: int = 5,
        with_answer: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a search query.

        Args:
            query: Search query text
            doc_ids: Optional list of document IDs to search
            top_k: Number of results to return
            with_answer: Whether to generate an LLM answer

        Returns:
            Search results with optional answer
        """
        data = {
            'query': query,
            'top_k': top_k,
            'with_answer': with_answer
        }
        if doc_ids:
            data['doc_ids'] = doc_ids

        return self._request("POST", "/search/search", json=data)

    # ========================================================================
    # Convenience Methods
    # ========================================================================

    def upload_and_index(
        self,
        file_path: str,
        doc_type: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a document and trigger indexing in one call.

        Args:
            file_path: Path to the document file
            doc_type: Document type ('pdf' or 'markdown')
            description: Optional document description

        Returns:
            Document and indexing information
        """
        # Upload document
        doc = self.upload_document(file_path, doc_type, description)
        doc_id = doc['id']

        # Index document
        index_result = self.index_document(doc_id)

        return {
            'document': doc,
            'index': index_result
        }

    def wait_for_indexing(
        self,
        doc_id: int,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for document indexing to complete.

        Args:
            doc_id: Document ID
            timeout: Maximum time to wait in seconds
            poll_interval: Polling interval in seconds

        Returns:
            Final document status

        Raises:
            TimeoutError: If indexing doesn't complete within timeout
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_document_status(doc_id)
            data = status.get('data', {})

            if data.get('status') in ['ready', 'error']:
                return status

            time.sleep(poll_interval)

        raise TimeoutError(f"Indexing timeout for document {doc_id}")

    def list_ready_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents that are ready for search.

        Returns:
            List of ready documents
        """
        result = self.list_documents(status='ready', limit=1000)
        return result.get('documents', [])


# ========================================================================
# Example Usage
# ========================================================================

if __name__ == "__main__":
    # Initialize client
    kb = KnowledgeBaseClient("http://localhost:8000")

    # Check health
    print("Health check:", kb.health_check())

    # Upload and index a document
    # result = kb.upload_and_index("example.pdf", "pdf")
    # print("Uploaded and indexed:", result)

    # Wait for indexing to complete
    # kb.wait_for_indexing(result['document']['id'])

    # Search
    # search_results = kb.search("What are the main findings?", top_k=3)
    # print("Search results:", search_results)
    # print("Answer:", search_results.get('answer'))

    # List all documents
    # docs = kb.list_documents()
    # print("Total documents:", docs['total'])
