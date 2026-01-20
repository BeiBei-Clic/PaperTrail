# PageIndex 知识库系统

基于 PageIndex 树状索引和 DeepSeek API 的智能文档检索系统。

## 功能特性

- 📄 支持多种文档格式（PDF、Markdown、TXT）
- 🌳 基于树状结构的智能索引
- 🔍 使用 LangChain Agent 的智能检索
- 🤖 集成 DeepSeek API
- 🚀 FastAPI Web 服务

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置 DeepSeek API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
```

### 3. 初始化数据库

```bash
python -m src.storage.database
```

### 4. 启动服务

```bash
python -m src.main
```

服务将在 `http://localhost:8000` 启动。

## API 文档

启动服务后，访问以下地址查看完整 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 使用示例

### 上传文档

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@example.pdf" \
  -F "doc_type=auto"
```

### 索引文档

```bash
curl -X POST "http://localhost:8000/api/documents/{doc_id}/index"
```

### 搜索（使用 Agent）

```bash
curl -X POST "http://localhost:8000/api/search/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "文档的主要结论是什么？",
    "top_k": 5
  }'
```

### 简单搜索

```bash
curl -X POST "http://localhost:8000/api/search/simple" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "关键词搜索",
    "top_k": 5
  }'
```

## 目录结构

```
src/
├── config/              # 配置管理
├── core/                # 核心业务逻辑
├── storage/             # 数据存储层
├── api/                 # API 服务层
├── agents/              # LangChain 智能体
├── adapters/            # 适配层
└── utils/               # 工具模块
```

## 技术栈

- **LLM**: DeepSeek API
- **LangChain**: v0.3+
- **Web 框架**: FastAPI
- **数据库**: SQLAlchemy + SQLite
- **文档处理**: PyMuPDF (PDF), Markdown

## 注意事项

1. 确保 DeepSeek API Key 已正确配置
2. 大文档索引可能需要较长时间
3. 建议在生产环境使用 PostgreSQL 而非 SQLite
4. LangChain Agent 搜索会比简单搜索消耗更多 token

## 许可证

MIT License
