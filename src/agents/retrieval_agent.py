"""检索智能体"""

from typing import Dict, Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from src.adapters.deepseek_client import DeepSeekClient
from src.agents.tools.content_extractor import (
    content_extractor,
    get_document_structure,
    get_node_path,
)
from src.agents.tools.tree_search_tool import simple_tree_search, tree_search
from src.config.prompts import PromptTemplates


class RetrievalAgent:
    """基于 LangChain 的检索智能体"""

    def __init__(self, session: Session):
        self.session = session
        self.client = DeepSeekClient()
        self.tools = self._create_tools()
        self.agent = self._create_agent()

    def _create_tools(self):
        """创建智能体工具"""
        return [
            tree_search,
            simple_tree_search,
            content_extractor,
            get_document_structure,
            get_node_path,
        ]

    def _create_agent(self):
        """创建智能体"""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PromptTemplates.get_retrieval_prompt("system")),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        agent = create_tool_calling_agent(
            llm=self.client.llm,
            tools=self.tools,
            prompt=prompt,
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
        )

    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """执行智能检索"""
        try:
            result = self.agent.invoke({"input": query})

            return {
                "query": query,
                "answer": result["output"],
                "intermediate_steps": self._format_steps(result.get("intermediate_steps", [])),
            }
        except Exception as e:
            return {
                "query": query,
                "answer": f"检索出错: {str(e)}",
                "error": str(e),
            }

    def _format_steps(self, steps):
        """格式化中间步骤"""
        formatted = []
        for step in steps:
            action, observation = step
            formatted.append(
                {
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                    "output": str(observation),
                }
            )
        return formatted

    async def asearch(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """异步执行智能检索"""
        try:
            result = await self.agent.ainvoke({"input": query})

            return {
                "query": query,
                "answer": result["output"],
                "intermediate_steps": self._format_steps(result.get("intermediate_steps", [])),
            }
        except Exception as e:
            return {
                "query": query,
                "answer": f"检索出错: {str(e)}",
                "error": str(e),
            }
