"""
SQLAdmin 认证后端
基于数据库用户的登录认证系统
"""

from typing import Optional
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from base import DATABASE_URL, get_db
from models.auth_model import User


class DatabaseAuthenticationBackend(AuthenticationBackend):
    """基于数据库的认证后端"""

    async def login(self, request: Request) -> bool:
        """登录处理"""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        # 验证用户凭据
        with next(get_db()) as db:
            user = db.query(User).filter(User.username == username).first()

            if user and user.verify_password(password) and user.is_active:
                # 登录成功，设置会话
                request.session.update(
                    {
                        "user_id": user.id,
                        "username": user.username,
                        "is_superuser": user.is_superuser,
                    }
                )
                return True

        return False

    async def logout(self, request: Request) -> bool:
        """登出处理"""
        # 清除会话
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """验证用户是否已登录"""
        user_id = request.session.get("user_id")
        if not user_id:
            return False

        # 验证用户是否仍然有效
        with next(get_db()) as db:
            user = (
                db.query(User)
                .filter(User.id == user_id, User.is_active == True)
                .first()
            )

            if user:
                # 更新请求中的用户信息
                request.state.user = user
                return True

        # 用户无效，清除会话
        request.session.clear()
        return False


class AdminAuthenticationBackend(DatabaseAuthenticationBackend):
    """管理员认证后端（只允许超级用户登录）"""

    async def authenticate(self, request: Request) -> bool:
        """验证用户是否已登录且为管理员"""
        # 首先进行基本认证
        if not await super().authenticate(request):
            return False

        # 检查是否为超级用户
        user = getattr(request.state, "user", None)
        if user and user.is_superuser:
            return True

        # 非管理员用户，清除会话
        request.session.clear()
        return False


class FlexibleAuthenticationBackend(DatabaseAuthenticationBackend):
    """灵活认证后端（允许所有有效用户登录，但根据权限控制访问）"""

    async def authenticate(self, request: Request) -> bool:
        """验证用户是否已登录"""
        # 使用基础认证，允许所有有效用户登录
        return await super().authenticate(request)


# 创建认证实例
auth_backend = DatabaseAuthenticationBackend(
    secret_key="your-secret-key-change-in-production"
)
admin_auth_backend = AdminAuthenticationBackend(
    secret_key="your-secret-key-change-in-production"
)
flexible_auth_backend = FlexibleAuthenticationBackend(
    secret_key="your-secret-key-change-in-production"
)
