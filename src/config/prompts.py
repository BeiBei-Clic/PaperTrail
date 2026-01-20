"""提示词模板"""

# 文档索引相关提示词
INDEXING_SYSTEM_PROMPT = """你是一个专业的文档索引专家。你的任务是将文档内容组织成树状结构，便于后续检索。

要求：
1. 分析文档的逻辑结构和层次关系
2. 识别章节、小节等标题
3. 为每个节点生成简洁的摘要
4. 保持层次清晰，便于检索"""

NODE_SUMMARY_PROMPT = """请为以下内容生成一个简洁的摘要（不超过100字）：

{content}

摘要："""

TREE_STRUCTURE_ANALYSIS_PROMPT = """请分析以下文档目录结构，识别出主要的章节和层次关系：

{toc}

请以 JSON 格式返回结构化数据，格式如下：
{{
    "title": "文档标题",
    "sections": [
        {{
            "level": 1,
            "title": "章节标题",
            "page_start": 页码,
            "children": [...]
        }}
    ]
}}"""


# 检索相关提示词
RETRIEVAL_SYSTEM_PROMPT = """你是一个专业的文档检索助手。你的任务是从文档库中找到与用户问题相关的信息。

可用工具：
1. tree_search: 在文档树结构中搜索相关节点
2. content_extractor: 提取指定节点的完整内容

工作流程：
1. 理解用户的问题
2. 使用 tree_search 工具找到相关文档节点
3. 使用 content_extractor 提取这些节点的内容
4. 基于提取的内容回答用户问题

重要提示：
- 请始终使用工具来获取信息，不要编造答案
- 如果找不到相关信息，明确告知用户
- 引用具体的内容来源，包括文档标题和章节
- 保持回答准确、客观"""

RETRIEVAL_QUERY_REPHRASE_PROMPT = """请将以下用户查询重写为更精确的搜索查询：

原始查询：{query}

上下文：{context}

重写后的查询："""

SEMANTIC_SEARCH_PROMPT = """基于以下问题，判断文档节点的相关性：

问题：{query}

节点信息：
- 标题：{title}
- 摘要：{summary}

请返回一个 0-10 之间的相关性分数，并简要说明理由。

分数：
理由："""


# Agent 工具提示词
TREE_SEARCH_TOOL_DESCRIPTION = """在文档树结构中搜索相关节点。
此工具会基于语义相似度找到与查询相关的文档节点。

参数：
- query: 搜索查询字符串
- doc_ids: 要搜索的文档ID列表（可选）
- top_k: 返回结果数量（默认5）

返回：相关节点列表，包含节点ID、标题、摘要等信息"""

CONTENT_EXTRACTOR_DESCRIPTION = """提取指定文档节点的完整内容。
此工具会获取节点的详细文本内容，用于回答用户问题。

参数：
- node_id: 节点ID

返回：节点的完整文本内容"""


# 文档分析提示词
DOCUMENT_TYPE_DETECTION_PROMPT = """分析以下文件，判断其文档类型：

文件信息：
- 文件名：{filename}
- 文件大小：{size} bytes
- 前1000字符：{preview}

请返回文档类型（pdf/markdown/txt/other）及简要说明。"""

SECTION_BOUNDARY_DETECTION_PROMPT = """判断以下内容是否为新的章节开始：

前一段标题：{previous_title}
当前内容：{current_content}

如果是新章节，请提取章节标题和级别。"""


# 答案生成提示词
ANSWER_GENERATION_PROMPT = """基于以下检索到的文档内容，回答用户问题。

用户问题：{query}

相关文档内容：
{context}

请生成准确、详细的答案，并引用具体的内容来源。如果内容不足以回答问题，请明确说明。"""


# Prompt 模板类
class PromptTemplates:
    """提示词模板集合"""

    INDEXING = {
        "system": INDEXING_SYSTEM_PROMPT,
        "node_summary": NODE_SUMMARY_PROMPT,
        "tree_structure": TREE_STRUCTURE_ANALYSIS_PROMPT,
    }

    RETRIEVAL = {
        "system": RETRIEVAL_SYSTEM_PROMPT,
        "query_rephrase": RETRIEVAL_QUERY_REPHRASE_PROMPT,
        "semantic_search": SEMANTIC_SEARCH_PROMPT,
        "answer_generation": ANSWER_GENERATION_PROMPT,
    }

    TOOLS = {
        "tree_search": TREE_SEARCH_TOOL_DESCRIPTION,
        "content_extractor": CONTENT_EXTRACTOR_DESCRIPTION,
    }

    DOCUMENT_ANALYSIS = {
        "type_detection": DOCUMENT_TYPE_DETECTION_PROMPT,
        "section_boundary": SECTION_BOUNDARY_DETECTION_PROMPT,
    }

    @classmethod
    def get_indexing_prompt(cls, prompt_type: str) -> str:
        """获取索引相关提示词"""
        return cls.INDEXING.get(prompt_type, "")

    @classmethod
    def get_retrieval_prompt(cls, prompt_type: str) -> str:
        """获取检索相关提示词"""
        return cls.RETRIEVAL.get(prompt_type, "")

    @classmethod
    def get_tool_description(cls, tool_name: str) -> str:
        """获取工具描述"""
        return cls.TOOLS.get(tool_name, "")
