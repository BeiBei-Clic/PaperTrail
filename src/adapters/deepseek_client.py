"""DeepSeek API 客户端"""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from src.config.settings import get_settings


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self):
        self.settings = get_settings()
        self._llm = None

    @property
    def llm(self) -> BaseChatModel:
        """获取 LangChain LLM 实例"""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.settings.deepseek_model,
                api_key=self.settings.deepseek_api_key,
                base_url=self.settings.deepseek_base_url,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.max_tokens,
                timeout=self.settings.request_timeout,
            )
        return self._llm

    def get_chat_model(self, temperature: float = None, max_tokens: int = None) -> BaseChatModel:
        """获取指定温度和最大 token 数的聊天模型"""
        return ChatOpenAI(
            model=self.settings.deepseek_model,
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url,
            temperature=temperature or self.settings.llm_temperature,
            max_tokens=max_tokens or self.settings.max_tokens,
            timeout=self.settings.request_timeout,
        )

    def invoke(self, prompt: str, temperature: float = None) -> str:
        """调用 LLM 并返回文本响应"""
        model = self.get_chat_model(temperature=temperature)
        response = model.invoke(prompt)
        return response.content

    async def ainvoke(self, prompt: str, temperature: float = None) -> str:
        """异步调用 LLM 并返回文本响应"""
        model = self.get_chat_model(temperature=temperature)
        response = await model.ainvoke(prompt)
        return response.content
