"""
数据库基础配置
"""

import os
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建基础模型类
Base = declarative_base()

# 数据库连接URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:123456@127.0.0.1:5432/pp_db"
)
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# 同步数据库引擎和会话（用于 FastAdmin）
postgres_engine_2 = create_engine(DATABASE_URL, echo=True)
PostgresSessionLocal2 = sessionmaker(
    autocommit=False, autoflush=False, bind=postgres_engine_2
)

# 异步数据库引擎和会话（用于 FastAPI 路由）
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


# 依赖项：获取数据库会话
def get_db():
    """获取同步数据库会话"""
    db = PostgresSessionLocal2()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


# 创建所有表
async def create_tables():
    """创建所有数据库表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 删除所有表
async def drop_tables():
    """删除所有数据库表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
