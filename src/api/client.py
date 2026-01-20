"""知识库客户端"""

from typing import Optional

import requests


class KnowledgeBaseClient:
    """知识库 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化客户端

        Args:
            base_url: API 基础 URL
        """
        self.base_url = base_url
        self.api_base = f"{base_url}/api"

    def upload_document(
        self,
        file_path: str,
        doc_type: str = "auto",
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """
        上传文档

        Args:
            file_path: 文件路径
            doc_type: 文档类型（auto, pdf, markdown, txt）
            title: 文档标题（可选）
            description: 文档描述（可选）

        Returns:
            上传的文档信息
        """
        url = f"{self.api_base}/documents/upload"

        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"doc_type": doc_type}
            if title:
                data["title"] = title
            if description:
                data["description"] = description

            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()

    def list_documents(self, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None) -> dict:
        """
        获取文档列表

        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            status_filter: 状态过滤

        Returns:
            文档列表
        """
        url = f"{self.api_base}/documents"
        params = {"skip": skip, "limit": limit}
        if status_filter:
            params["status"] = status_filter

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_document(self, document_id: int) -> dict:
        """
        获取文档详情

        Args:
            document_id: 文档 ID

        Returns:
            文档详情
        """
        url = f"{self.api_base}/documents/{document_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def delete_document(self, document_id: int) -> dict:
        """
        删除文档

        Args:
            document_id: 文档 ID

        Returns:
            删除结果
        """
        url = f"{self.api_base}/documents/{document_id}"
        response = requests.delete(url)
        response.raise_for_status()
        return response.json()

    def index_document(self, document_id: int) -> dict:
        """
        索引文档

        Args:
            document_id: 文档 ID

        Returns:
            索引结果
        """
        url = f"{self.api_base}/documents/{document_id}/index"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()

    def get_document_status(self, document_id: int) -> dict:
        """
        获取文档索引状态

        Args:
            document_id: 文档 ID

        Returns:
            文档状态
        """
        url = f"{self.api_base}/documents/{document_id}/status"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def search(
        self,
        query: str,
        doc_ids: Optional[list] = None,
        top_k: int = 5,
        search_type: str = "agent",
    ) -> dict:
        """
        搜索文档

        Args:
            query: 搜索查询
            doc_ids: 要搜索的文档 ID 列表（可选）
            top_k: 返回结果数量
            search_type: 搜索类型（agent 或 simple）

        Returns:
            搜索结果
        """
        url = f"{self.api_base}/search/{search_type}"
        data = {"query": query, "doc_ids": doc_ids, "top_k": top_k}

        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_node(self, node_id: str) -> dict:
        """
        获取节点完整内容

        Args:
            node_id: 节点 ID

        Returns:
            节点内容
        """
        url = f"{self.api_base}/search/node/{node_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_node_path(self, node_id: str) -> list:
        """
        获取节点路径

        Args:
            node_id: 节点 ID

        Returns:
            节点路径列表
        """
        url = f"{self.api_base}/search/node/{node_id}/path"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_document_structure(self, document_id: int) -> list:
        """
        获取文档树状结构

        Args:
            document_id: 文档 ID

        Returns:
            文档树状结构
        """
        url = f"{self.api_base}/search/document/{document_id}/structure"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


# 使用示例
if __name__ == "__main__":
    client = KnowledgeBaseClient()

    # 上传文档
    # doc = client.upload_document("example.pdf")
    # print(f"上传成功: {doc}")

    # 索引文档
    # result = client.index_document(doc["id"])
    # print(f"索引结果: {result}")

    # 搜索
    # result = client.search("文档的主要结论是什么？")
    # print(f"搜索结果: {result['answer']}")
