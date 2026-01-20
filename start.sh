#!/bin/bash

# PageIndex Docker 一键启动脚本

echo "=========================================="
echo "  PageIndex Docker 启动脚本"
echo "=========================================="

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "错误: .env 文件不存在"
    echo "请先复制 .env.example 为 .env 并配置必要的环境变量："
    echo "  cp .env.example .env"
    echo "  编辑 .env 文件，设置 DEEPSEEK_API_KEY 和 POSTGRES_PASSWORD"
    exit 1
fi

# 加载 .env 文件
source .env

# 验证必需的环境变量
if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
    echo "错误: DEEPSEEK_API_KEY 未设置或无效"
    echo "请在 .env 文件中设置有效的 DEEPSEEK_API_KEY"
    exit 1
fi

if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_password_here" ]; then
    echo "错误: POSTGRES_PASSWORD 未设置或无效"
    echo "请在 .env 文件中设置安全的 POSTGRES_PASSWORD"
    exit 1
fi

echo "环境变量检查通过"
echo "  DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:0:10}..."
echo "  POSTGRES_PASSWORD: ***"
echo ""

# 停止旧容器
echo "停止旧容器..."
docker-compose down 2>/dev/null

# 构建镜像
echo "构建 Docker 镜像..."
docker-compose build

# 启动服务
echo ""
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "服务状态："
docker-compose ps

echo ""
echo "=========================================="
echo "  服务启动成功！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - API 文档: http://localhost:8000/docs"
echo "  - 根路径:   http://localhost:8000"
echo "  - 健康检查: http://localhost:8000/health"
echo ""
echo "查看日志："
echo "  docker-compose logs -f app"
echo ""
echo "停止服务："
echo "  docker-compose down"
echo ""
