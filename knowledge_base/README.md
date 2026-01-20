# PageIndex 知识库

基于 PageIndex 树状索引和 LLM 检索的本地知识库部署系统。所有数据本地存储，无需向量数据库和文档分块。

## 特性

- **无需向量数据库**：使用基于树的索引和 LLM 推理进行检索
- **本地优先**：所有数据存储在本地，支持离线使用
- **模块化设计**：核心、存储、API、配置清晰分离
- **易于部署**：支持 Docker 或直接 Python 运行
- **RESTful API**：完整的文档管理和搜索 API
- **多格式支持**：支持 PDF 和 Markdown 文档

## 架构

```
knowledge_base/
├── core/                  # 核心业务逻辑
│   ├── document_manager.py    # 文档管理
│   ├── index_engine.py        # PageIndex 集成
│   ├── retrieval_engine.py    # 搜索和检索
│   └── tree_search.py         # 树搜索工具
│
├── storage/               # 数据持久化层
│   ├── database.py            # 数据库封装
│   ├── models.py              # SQLAlchemy 模型
│   └── file_storage.py        # 文件存储管理
│
├── api/                   # FastAPI Web 服务
│   ├── app.py                 # 应用入口
│   ├── routes/                # API 路由
│   │   ├── documents.py       # 文档管理端点
│   │   └── search.py          # 搜索端点
│   └── schemas.py             # Pydantic 模型
│
├── config/                # 配置
│   ├── settings.py            # 设置管理
│   └── default_config.yaml    # 默认配置
│
├── scripts/               # 工具脚本
│   ├── init_db.py             # 数据库初始化
│   └── batch_import.py        # 批量导入文档
│
└── data/                  # 数据目录
    ├── documents/             # 存储的文档
    └── knowledge_base.db      # SQLite 数据库
```

## 安装

### 前置要求

- Python 3.8+
- OpenAI API 密钥

### 安装步骤

1. **安装依赖**：

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装知识库依赖
pip install -r knowledge_base/requirements_kb.txt
```

2. **配置环境**：

```bash
# 复制环境变量示例文件
cp knowledge_base/.env.example knowledge_base/.env

# 编辑 knowledge_base/.env 并添加你的 OpenAI API 密钥
# 必填：OPENAI_API_KEY=your_key_here
```

3. **初始化数据库**：

```bash
python -m knowledge_base.scripts.init_db
```

4. **启动 API 服务器**：

```bash
# 开发模式
uvicorn knowledge_base.api.app:app --reload --host 0.0.0.0 --port 8000

# 或使用内置启动器
python -m knowledge_base.api.app
```

API 访问地址：`http://localhost:8000`
交互式 API 文档：`http://localhost:8000/api/docs`

## 快速开始

### 1. 上传文档

```bash
# 上传 PDF 文档
curl -X POST "http://localhost:8000/api/documents/upload?doc_type=pdf" \
  -F "file=@example.pdf"

# 上传 Markdown 文档
curl -X POST "http://localhost:8000/api/documents/upload?doc_type=markdown" \
  -F "file=@example.md"
```

### 2. 索引文档

```bash
# 索引指定文档
curl -X POST "http://localhost:8000/api/documents/{doc_id}/index"
```

### 3. 搜索

```bash
# 搜索所有文档
curl -X POST "http://localhost:8000/api/search/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "主要发现是什么？",
    "top_k": 5,
    "with_answer": true
  }'
```

## 批量导入

从目录批量导入文档：

```bash
# 从目录导入（自动检测文件类型）
python -m knowledge_base.scripts.batch_import /path/to/documents

# 递归导入仅 PDF 文件
python -m knowledge_base.scripts.batch_import /path/to/documents --type pdf -r

# 导入但不建立索引
python -m knowledge_base.scripts.batch_import /path/to/documents --no-index
```

## API 文档

### 文档管理端点

#### 上传文档
```
POST /api/documents/upload
Content-Type: multipart/form-data

参数：
- file: 文档文件（PDF 或 Markdown）
- doc_type: "pdf" 或 "markdown"
- description: (可选) 文档描述
```

#### 获取文档
```
GET /api/documents/{doc_id}
```

#### 列出文档
```
GET /api/documents?skip=0&limit=100&status=ready&doc_type=pdf
```

#### 删除文档
```
DELETE /api/documents/{doc_id}
```

#### 获取文档状态
```
GET /api/documents/{doc_id}/status
```

#### 索引文档
```
POST /api/documents/{doc_id}/index
```

#### 重新索引文档
```
POST /api/documents/{doc_id}/reindex
```

### 搜索端点

#### 搜索
```
POST /api/search/search
Content-Type: application/json

请求体：
{
  "query": "搜索查询",
  "doc_ids": [1, 2, 3],  // 可选：指定文档
  "top_k": 5,              // 返回结果数量
  "with_answer": true      // 是否生成 LLM 答案
}

响应：
{
  "query": "搜索查询",
  "results": [
    {
      "document_id": 1,
      "doc_name": "example.pdf",
      "doc_type": "pdf",
      "node": {
        "node_id": "0001",
        "title": "章节标题",
        "summary": "章节摘要",
        "page_index": [10, 15],
        "line_num": 123
      },
      "content": "完整文本内容...",
      "score": 0.95
    }
  ],
  "answer": "基于结果生成的答案...",
  "latency_ms": 1500.5
}
```

## 配置

`knowledge_base/.env` 中的关键配置选项：

| 设置 | 描述 | 默认值 |
|---------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API 密钥（必填） | - |
| `OPENAI_MODEL` | 使用的 LLM 模型 | `gpt-4o-2024-11-20` |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/knowledge_base.db` |
| `STORAGE_PATH` | 文档存储目录 | `./data/documents` |
| `MAX_FILE_SIZE` | 最大上传大小（字节） | `104857600` (100MB) |
| `DEFAULT_TOP_K` | 默认搜索结果数 | `5` |
| `MAX_CONTEXT_TOKENS` | 答案生成的最大 token 数 | `16000` |

## 工作原理

### 1. 文档索引

1. **上传**：文档上传并保存到存储
2. **解析**：PageIndex 解析文档结构
   - PDF：提取目录并构建层次树
   - Markdown：使用标题结构构建树
3. **增强**：LLM 为每个节点生成摘要
4. **存储**：树结构持久化到数据库

### 2. 搜索和检索

1. **查询**：用户提交搜索查询
2. **树搜索**：LLM 分析查询和树节点摘要以找到相关章节
3. **内容提取**：从相关节点提取完整文本
4. **答案生成**：LLM 基于提取的内容生成答案

### 相比向量搜索的优势

- **无需分块**：保留文档结构和上下文
- **层次化**：维护文档组织（章节、段落）
- **推理能力**：使用 LLM 理解查询意图和节点关系
- **可解释性**：可以追踪使用了哪些章节来生成答案

## 数据模型

### 文档模型
```python
{
  "id": 1,
  "doc_name": "example.pdf",
  "doc_type": "pdf",
  "file_size": 1048576,
  "page_count": 100,
  "status": "ready",  # pending, indexing, ready, error
  "indexed_at": "2024-01-20T10:30:00"
}
```

### 树结构
```python
{
  "doc_name": "example.pdf",
  "structure": [
    {
      "node_id": "0001",
      "title": "第一章",
      "summary": "主题介绍",
      "page_index": [1, 10],
      "text": "完整章节内容...",
      "nodes": [
        {
          "node_id": "0002",
          "title": "1.1 节",
          "summary": "详细说明",
          "page_index": [2, 5],
          "text": "章节内容...",
          "nodes": []
        }
      ]
    }
  ]
}
```

## 部署

### 开发环境

```bash
uvicorn knowledge_base.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境

```bash
uvicorn knowledge_base.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker（即将推出）

```bash
docker-compose up -d
```

## 性能考虑

### 索引时间

- **小型文档**（< 10 页）：约 30 秒
- **中型文档**（10-50 页）：约 1-2 分钟
- **大型文档**（> 50 页）：约 3-5 分钟

索引时间取决于：
- 文档长度和复杂度
- OpenAI API 响应时间
- 网络延迟

### 搜索时间

- **典型搜索**：2-5 秒
- **包含答案生成**：+1-3 秒

搜索性能取决于：
- 已索引文档数量
- Top-K 参数
- OpenAI API 响应时间

### 成本优化

1. **批量索引**：一次索引多个文档
2. **缓存结果**：存储频繁查询
3. **使用更小的模型**：大规模部署使用更快的模型
4. **限制上下文**：调整 `MAX_CONTEXT_TOKENS` 以降低成本

## 故障排除

### OpenAI API 错误

**错误**："OpenAI API key not configured"
**解决方案**：在 `knowledge_base/.env` 中设置 `OPENAI_API_KEY`

**错误**："Rate limit exceeded"
**解决方案**：等待片刻后重试，或升级 OpenAI 计划

### 索引失败

**错误**："Failed to index document"
**解决方案**：
- 检查文档格式（PDF 必须是文本格式，不是扫描图片）
- 验证 OpenAI API 密钥是否有效
- 检查 `logs/knowledge_base.log` 日志

### 无搜索结果

**可能原因**：
- 文档未索引（使用 `/api/documents/{id}/status` 检查状态）
- 查询过于具体（尝试更宽泛的关键词）
- 文档不包含相关内容

## 扩展系统

### 添加文档类型

1. 在 `core/index_engine.py` 中实现解析器
2. 在 `api/schemas.py` 中添加类型验证
3. 更新文档

### 自定义搜索算法

扩展 `core/retrieval_engine.py` 中的 `RetrievalEngine`：
- 添加关键词搜索后备
- 实现混合检索
- 添加相关性评分

### Web UI

可以使用以下框架构建 Web 前端：
- Vue 3 + Element Plus
- React + Material-UI
- 任何可以消费 REST API 的框架

## Python 客户端示例

```python
from knowledge_base.client import KnowledgeBaseClient

# 初始化客户端
kb = KnowledgeBaseClient("http://localhost:8000")

# 上传并索引文档
result = kb.upload_and_index("example.pdf", "pdf")
print(f"文档已上传: {result['document']['id']}")

# 等待索引完成
kb.wait_for_indexing(result['document']['id'])

# 搜索
search_results = kb.search("主要发现是什么？", top_k=3)
print(f"答案: {search_results['answer']}")

# 列出所有文档
docs = kb.list_ready_documents()
print(f"共有 {len(docs)} 个已索引文档")
```

## 许可证

本模块是 PageIndex 项目的一部分。详情请参见主 LICENSE 文件。

## 贡献

欢迎贡献！请阅读主项目的 CONTRIBUTING.md 了解指南。

## 支持

如有问题和疑问：
- GitHub Issues：[PageIndex Issues](https://github.com/your-org/pageindex/issues)
- 文档：参见主项目 README

## 致谢

基于 [PageIndex](https://github.com/your-org/pageindex) 构建，这是一个使用 LLM 推理的基于树的文档索引系统。
