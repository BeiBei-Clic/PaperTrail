# PostgreSQL 配置指南

本指南帮助您配置 PageIndex 知识库系统使用 PostgreSQL 数据库。

## 安装 PostgreSQL

### Windows

1. 下载 PostgreSQL 安装程序：https://www.postgresql.org/download/windows/
2. 运行安装程序，记住设置的密码
3. 默认端口：5432

### macOS

```bash
# 使用 Homebrew
brew install postgresql@16
brew services start postgresql@16
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Docker (推荐)

```bash
docker run --name pageindex-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=pageindex_kb \
  -p 5432:5432 \
  -v pageindex_data:/var/lib/postgresql/data \
  -d postgres:16
```

## 创建数据库

### 方法 1: 使用命令行

```bash
# Windows
psql -U postgres
CREATE DATABASE pageindex_kb;
\q

# macOS/Linux
sudo -u postgres createdb pageindex_kb
```

### 方法 2: 使用 Docker

```bash
docker exec -it pageindex-postgres psql -U postgres -c "CREATE DATABASE pageindex_kb;"
```

## 配置环境变量

在项目根目录创建 `.env` 文件：

### 本地 PostgreSQL

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/pageindex_kb
```

### Docker PostgreSQL

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pageindex_kb
```

### 云 PostgreSQL (Supabase/Neon/Railway)

从服务商获取连接字符串，格式类似：

```env
DATABASE_URL=postgresql://user:password@host.railway.app:5432/railway
```

## 安装依赖

```bash
uv pip install psycopg2-binary
```

或安装所有依赖：

```bash
uv pip install -r requirements.txt
```

## 初始化数据库

```bash
python -m src.storage.database
```

## 验证安装

```bash
python -m src.main
```

访问 http://localhost:8000/docs 测试 API。

## 从 SQLite 迁移数据

### 方法 1: 使用 pgloader (推荐)

```bash
pgloader sqlite:///data/knowledge_base.db postgresql://postgres@localhost/pageindex_kb
```

### 方法 2: 手动导出导入

1. 从 SQLite 导出数据为 JSON
2. 使用 API 导入到 PostgreSQL

## 常见问题

### 连接失败

- 检查 PostgreSQL 服务是否运行
- 验证 DATABASE_URL 中的用户名和密码
- 检查防火墙设置

### 权限错误

```sql
-- 授予用户权限
GRANT ALL PRIVILEGES ON DATABASE pageindex_kb TO your_user;
```

### Windows psycopg2 安装失败

使用预编译的二进制包：

```bash
uv pip install psycopg2-binary
```

## 性能优化 (可选)

### 连接池配置

在 `src/storage/database.py` 中调整连接池参数：

```python
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### 启用 pgvector (用于向量搜索)

```sql
CREATE EXTENSION vector;
```

## 备份与恢复

### 备份

```bash
pg_dump -U postgres pageindex_kb > backup.sql
```

### 恢复

```bash
psql -U postgres pageindex_kb < backup.sql
```
