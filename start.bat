@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   PageIndex Docker 启动脚本
echo ==========================================
echo.

REM 检查 .env 文件是否存在
if not exist .env (
    echo 错误: .env 文件不存在
    echo 请先复制 .env.example 为 .env 并配置必要的环境变量：
    echo   copy .env.example .env
    echo   编辑 .env 文件，设置 DEEPSEEK_API_KEY 和 POSTGRES_PASSWORD
    exit /b 1
)

REM 读取并验证 DEEPSEEK_API_KEY
findstr /B "DEEPSEEK_API_KEY=" .env >nul
if errorlevel 1 (
    echo 错误: .env 文件中未找到 DEEPSEEK_API_KEY
    exit /b 1
)

REM 读取并验证 POSTGRES_PASSWORD
findstr /B "POSTGRES_PASSWORD=" .env >nul
if errorlevel 1 (
    echo 错误: .env 文件中未找到 POSTGRES_PASSWORD
    exit /b 1
)

echo 环境变量检查通过
echo.

REM 停止旧容器
echo 停止旧容器...
docker-compose down 2>nul

REM 构建镜像
echo 构建 Docker 镜像...
docker-compose build

REM 启动服务
echo.
echo 启动服务...
docker-compose up -d

REM 等待服务启动
echo.
echo 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo.
echo 服务状态：
docker-compose ps

echo.
echo ==========================================
echo   服务启动成功！
echo ==========================================
echo.
echo 访问地址：
echo   - API 文档: http://localhost:8000/docs
echo   - 根路径:   http://localhost:8000
echo   - 健康检查: http://localhost:8000/health
echo.
echo 查看日志：
echo   docker-compose logs -f app
echo.
echo 停止服务：
echo   docker-compose down
echo.

endlocal
