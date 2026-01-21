"""LangChain 与 PageIndex 的适配器"""

import asyncio
from typing import Dict, Any, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.adapters.deepseek_client import DeepSeekClient


class LangChainPageIndexAdapter:
    """LangChain 与 PageIndex 的适配器"""

    def __init__(self):
        self.client = DeepSeekClient()

    def call_llm(self, model: str, prompt: str, temperature: float = 0.0, **kwargs) -> str:
        """调用 LLM（同步）"""
        return self.client.invoke(prompt, temperature=temperature)

    async def call_llm_async(self, model: str, prompt: str, temperature: float = 0.0, **kwargs) -> str:
        """调用 LLM（异步）"""
        return await self.client.ainvoke(prompt, temperature=temperature)

    def call_llm_with_json(self, prompt: str, temperature: float = 0.0) -> Dict:
        """调用 LLM 并返回 JSON"""
        model = self.client.get_chat_model(temperature=temperature)

        chain = (
            ChatPromptTemplate.from_template("{prompt}")
            | model
            | JsonOutputParser()
        )

        return chain.invoke({"prompt": prompt})

    async def acall_llm_with_json(self, prompt: str, temperature: float = 0.0) -> Dict:
        """异步调用 LLM 并返回 JSON"""
        model = self.client.get_chat_model(temperature=temperature)

        chain = (
            ChatPromptTemplate.from_template("{prompt}")
            | model
            | JsonOutputParser()
        )

        return await chain.ainvoke({"prompt": prompt})

    def inject_to_pageindex(self):
        """将适配器注入到 PageIndex 环境"""
        import sys
        import pageindex.utils as utils

        # Monkey patch ChatGPT_API 函数
        utils.ChatGPT_API = self.call_llm
        utils.ChatGPT_API_async = self.call_llm_async

        # 如果需要，也可以注入到全局命名空间
        sys.modules["pageindex_adapter"] = self
