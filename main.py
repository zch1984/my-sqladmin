"""
SQLAdmin 管理界面主应用
"""

from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy import create_engine
from starlette.middleware.sessions import SessionMiddleware

from config import settings, get_admin_config
from base import DATABASE_URL
from models.auth_model import User, AuthCredentials
from admin.auth_admin import UserAdmin, AuthCredentialsAdmin
from auth.authentication import admin_auth_backend

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
)

# 添加会话中间件（认证所需）
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-change-in-production",
    max_age=3600,  # 1小时会话过期
)

# 创建数据库引擎（SQLAdmin需要同步引擎）
engine = create_engine(DATABASE_URL, echo=settings.database_echo)

# 创建Admin实例
admin = Admin(
    app=app,
    engine=engine,
    title=settings.admin_title,
    # 启用身份验证
    authentication_backend=admin_auth_backend,
)

# 注册模型管理器
admin.add_view(UserAdmin)
admin.add_view(AuthCredentialsAdmin)


# 根路径重定向到管理界面
@app.get("/")
async def root():
    """根路径重定向到管理界面"""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/admin")


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "SQLAdmin 管理系统运行正常"}


# API路由（可选）
@app.get("/api/users/count")
async def get_users_count():
    """获取用户总数"""
    from base import get_db
    from sqlalchemy import func

    with next(get_db()) as db:
        count = db.query(func.count(User.id)).scalar()
        return {"count": count}


@app.get("/api/credentials/count")
async def get_credentials_count():
    """获取认证凭据总数"""
    from base import get_db
    from sqlalchemy import func

    with next(get_db()) as db:
        count = db.query(func.count(AuthCredentials.id)).scalar()
        return {"count": count}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
