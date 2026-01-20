#!/bin/bash
# PostgreSQL 数据库初始化脚本

set -e

echo "=== PageIndex PostgreSQL 初始化 ==="
echo

# 配置（可根据需要修改）
DB_NAME=${DB_NAME:-pageindex_kb}
DB_USER=${DB_USER:-postgres}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

# 检查 PostgreSQL 是否运行
echo "1. 检查 PostgreSQL 服务..."
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; then
    echo "错误: PostgreSQL 服务未运行"
    echo "请先启动 PostgreSQL 服务："
    echo "  macOS: brew services start postgresql@16"
    echo "  Linux: sudo systemctl start postgresql"
    echo "  Docker: docker start pageindex-postgres"
    exit 1
fi
echo "PostgreSQL 服务运行正常"

# 检查数据库是否存在，不存在则创建
echo
echo "2. 检查数据库 $DB_NAME..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "数据库 $DB_NAME 已存在"
else
    echo "创建数据库 $DB_NAME..."
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    echo "数据库创建成功"
fi

# 安装依赖
echo
echo "3. 安装 PostgreSQL 驱动..."
uv pip install psycopg2-binary

# 初始化表结构
echo
echo "4. 初始化表结构..."
uv run python -m src.storage.database

# 验证连接
echo
echo "5. 验证数据库连接..."
uv run python -c "
from src.storage.database import get_engine
try:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute('SELECT version()')
        print('数据库连接成功')
        print('PostgreSQL 版本:', result.fetchone()[0])
except Exception as e:
    print('数据库连接失败:', e)
    exit(1)
"

echo
echo "=== 初始化完成 ==="
echo "数据库配置: postgresql://$DB_USER@***:$DB_PORT/$DB_NAME"
