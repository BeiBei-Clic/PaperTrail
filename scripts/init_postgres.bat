@echo off
REM PostgreSQL 数据库初始化脚本 (Windows)

echo === PageIndex PostgreSQL 初始化 ===
echo.

set DB_NAME=pageindex_kb
set DB_USER=postgres
set DB_HOST=localhost
set DB_PORT=5432

REM 检查 PostgreSQL 是否运行
echo 1. 检查 PostgreSQL 服务...
pg_isready -h %DB_HOST% -p %DB_PORT% >nul 2>&1
if errorlevel 1 (
    echo 错误: PostgreSQL 服务未运行
    echo 请先启动 PostgreSQL 服务：
    echo   服务管理器: 启动 postgresql-x64-16 服务
    echo   或使用 Docker: docker start pageindex-postgres
    exit /b 1
)
echo PostgreSQL 服务运行正常

REM 检查数据库是否存在
echo.
echo 2. 检查数据库 %DB_NAME%...
psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -lqt | findstr /C:"%DB_NAME%" >nul
if errorlevel 1 (
    echo 创建数据库 %DB_NAME%...
    createdb -h %DB_HOST% -p %DB_PORT% -U %DB_USER% %DB_NAME%
    echo 数据库创建成功
) else (
    echo 数据库 %DB_NAME% 已存在
)

REM 安装依赖
echo.
echo 3. 安装 PostgreSQL 驱动...
uv pip install psycopg2-binary

REM 初始化表结构
echo.
echo 4. 初始化表结构...
uv run python -m src.storage.database

REM 验证连接
echo.
echo 5. 验证数据库连接...
echo from src.storage.database import get_engine > temp_check.py
echo engine = get_engine() >> temp_check.py
echo with engine.connect() as conn: >> temp_check.py
echo     result = conn.execute('SELECT version()') >> temp_check.py
echo     print('数据库连接成功') >> temp_check.py
echo     print('PostgreSQL 版本:', result.fetchone()[0]) >> temp_check.py
uv run python temp_check.py
del temp_check.py

echo.
echo === 初始化完成 ===
echo 数据库配置: postgresql://%DB_USER%@***:%DB_PORT%/%DB_NAME%
pause
