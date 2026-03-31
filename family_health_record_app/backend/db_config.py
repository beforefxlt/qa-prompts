"""PostgreSQL 生产环境配置

使用说明:
1. 设置环境变量 DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/health_record
2. 运行 alembic upgrade head 创建表
3. 后续模型变更使用 alembic revision --autogenerate -m "描述" 生成迁移
4. 运行 alembic upgrade head 应用迁移

开发环境仍使用 SQLite:
- 不设置 DATABASE_URL 或设置为 sqlite+aiosqlite:///./health_record.db
"""

import os

# 生产环境配置示例
POSTGRES_CONFIG = {
    "DATABASE_URL": os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/health_record"
    ),
    # PostgreSQL 连接池配置
    "POOL_SIZE": int(os.getenv("DB_POOL_SIZE", "10")),
    "MAX_OVERFLOW": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "POOL_TIMEOUT": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    "POOL_RECYCLE": int(os.getenv("DB_POOL_RECYCLE", "1800")),
}

# SQLite 开发环境配置（默认）
SQLITE_CONFIG = {
    "DATABASE_URL": "sqlite+aiosqlite:///./health_record.db",
}


def get_db_config():
    """根据环境变量返回数据库配置"""
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgresql"):
        return POSTGRES_CONFIG
    return SQLITE_CONFIG
