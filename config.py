"""
应用配置文件
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""

    # 应用基本设置
    app_name: str = "SQLAdmin 用户认证管理系统"
    app_version: str = "1.0.0"
    app_description: str = "基于SQLAdmin和FastAPI的用户认证管理系统"

    # 服务器设置
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    reload: bool = True

    # 数据库设置
    database_url: str = "postgresql://postgres:123456@127.0.0.1:5432/pp_db"
    database_echo: bool = True

    # 管理界面设置
    admin_title: str = "用户认证管理系统"
    admin_logo_url: str = "https://preview.tabler.io/static/logo.svg"
    admin_base_url: str = "/admin"

    # 安全设置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # 分页设置
    default_page_size: int = 20
    max_page_size: int = 100

    # 文件上传设置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".pdf",
        ".txt",
        ".csv",
        ".xlsx",
    ]

    # 邮件设置（可选）
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True

    # 日志设置
    log_level: str = "INFO"
    log_file: Optional[str] = "app.log"

    # 缓存设置
    redis_url: Optional[str] = None
    cache_expire: int = 3600  # 1小时

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局设置实例
settings = Settings()


def get_database_url() -> str:
    """获取数据库连接URL"""
    return settings.database_url


def get_async_database_url() -> str:
    """获取异步数据库连接URL"""
    return settings.database_url.replace("postgresql://", "postgresql+asyncpg://")


def get_admin_config() -> dict:
    """获取管理界面配置"""
    return {
        "title": settings.admin_title,
        "logo_url": settings.admin_logo_url,
        "base_url": settings.admin_base_url,  # 修改为 base_url
        # 移除可能不支持的参数
        # "templates_dir": "templates",
        # "statics_dir": "static",
        # "custom_css_url": "/static/custom.css",
        # "custom_js_url": "/static/custom.js",
    }


def get_pagination_config() -> dict:
    """获取分页配置"""
    return {
        "page_size": settings.default_page_size,
        "page_size_options": [10, 20, 50, 100],
        "max_page_size": settings.max_page_size,
    }
