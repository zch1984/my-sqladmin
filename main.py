"""
完整权限管理的SQLAdmin主应用
完全基于SQLAdmin官方最佳实践实现的权限控制系统

功能特点：
1. 超级用户可以看到和修改所有信息
2. 普通用户只能看到自己的用户信息
3. 普通用户只能看到自己的私有认证凭据（可编辑删除）和公开认证凭据（只读）
4. 所有权限控制都在查询层面实现，确保数据安全
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import json
import logging

from config import settings, get_admin_config
from base import DATABASE_URL, postgres_engine_2
from models.auth_model import User, AuthCredentials
from admin.auth_admin_final import (
    UserPermissionAdmin,
    CredentialsPermissionAdmin,
    PermissionError,
)
from auth.authentication import flexible_auth_backend

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PermissionMiddleware(BaseHTTPMiddleware):
    """权限检查中间件 - 处理权限错误"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except PermissionError as e:
            logger.warning(
                f"权限错误: {e.message} - 用户: {getattr(request.state, 'user', 'Unknown')}"
            )

            # 如果是API请求，返回JSON错误
            if request.url.path.startswith("/api/"):
                return Response(
                    content=json.dumps({"error": e.message}),
                    status_code=403,
                    media_type="application/json",
                )
            # 如果是管理界面请求，返回友好的错误页面
            else:
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>访问被拒绝</title>
                    <meta charset="utf-8">
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif; 
                            margin: 40px;
                            background-color: #f8f9fa;
                        }}
                        .error-container {{ 
                            max-width: 600px; 
                            margin: 0 auto; 
                            text-align: center;
                            background: white;
                            padding: 40px;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }}
                        .error-code {{ 
                            font-size: 72px; 
                            color: #dc3545; 
                            margin: 20px 0;
                            font-weight: bold;
                        }}
                        .error-message {{ 
                            font-size: 24px; 
                            color: #495057; 
                            margin: 20px 0;
                        }}
                        .error-description {{ 
                            font-size: 16px; 
                            color: #6c757d; 
                            margin: 20px 0;
                            line-height: 1.5;
                        }}
                        .back-link {{ 
                            margin-top: 30px; 
                        }}
                        .back-link a {{ 
                            color: #007bff; 
                            text-decoration: none;
                            font-weight: bold;
                            padding: 10px 20px;
                            border: 2px solid #007bff;
                            border-radius: 5px;
                            transition: all 0.3s;
                        }}
                        .back-link a:hover {{ 
                            background-color: #007bff;
                            color: white;
                        }}
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <div class="error-code">403</div>
                        <div class="error-message">访问被拒绝</div>
                        <div class="error-description">{e.message}</div>
                        <div class="back-link">
                            <a href="/admin">返回管理界面</a>
                        </div>
                    </div>
                </body>
                </html>
                """
                return HTMLResponse(content=error_html, status_code=403)


# 创建FastAPI应用
app = FastAPI(
    title=f"{settings.app_name} - 完整权限管理版",
    description=f"{settings.app_description} - 基于SQLAdmin官方最佳实践的完整权限控制",
    version=settings.app_version,
    debug=settings.debug,
)

# 添加会话中间件（认证所需）
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-change-in-production",
    max_age=3600,  # 1小时会话过期
)

# 添加权限检查中间件
app.add_middleware(PermissionMiddleware)

# 使用统一的数据库引擎（与base.py保持一致）
engine = postgres_engine_2

# 创建Admin实例，使用灵活认证后端
admin = Admin(
    app=app,
    engine=engine,
    title=f"{settings.admin_title} - 完整权限管理版",
    # 使用灵活认证后端，允许所有有效用户登录
    authentication_backend=flexible_auth_backend,
)

# 注册完整权限管理的模型管理器
admin.add_view(UserPermissionAdmin)
admin.add_view(CredentialsPermissionAdmin)

logger.info("已注册完整权限管理界面")


# 根路径重定向到管理界面
@app.get("/")
async def root():
    """根路径重定向到管理界面"""
    return RedirectResponse(url="/admin")


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "message": "SQLAdmin 完整权限管理系统运行正常",
        "features": [
            "超级用户完全权限",
            "普通用户受限访问",
            "查询层面权限过滤",
            "细粒度字段控制",
        ],
    }


# API路由 - 带权限控制
@app.get("/api/user/profile")
async def get_user_profile(request: Request):
    """获取当前用户信息"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_superuser": user.is_superuser,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "permissions": {
            "can_see_all_users": user.is_superuser,
            "can_create_users": user.is_superuser,
            "can_see_all_credentials": user.is_superuser,
            "can_create_public_credentials": user.is_superuser,
        },
    }


@app.get("/api/users/count")
async def get_users_count(request: Request):
    """获取用户总数（根据权限过滤）"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    from base import get_db
    from sqlalchemy import func

    with next(get_db()) as db:
        if user.is_superuser:
            # 超级用户看到所有用户数量
            count = db.query(func.count(User.id)).scalar()
        else:
            # 普通用户只能看到自己，所以数量是1
            count = 1

        return {"count": count, "is_filtered": not user.is_superuser}


@app.get("/api/credentials/count")
async def get_credentials_count(request: Request):
    """获取认证凭据总数（根据权限过滤）"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    from base import get_db
    from sqlalchemy import func, or_, and_
    from models.auth_model import InfoStatusTypeEnum

    with next(get_db()) as db:
        if user.is_superuser:
            # 超级用户看到所有凭据数量
            count = db.query(func.count(AuthCredentials.id)).scalar()
        else:
            # 普通用户只能看到公开凭据和自己的私有凭据
            count = (
                db.query(func.count(AuthCredentials.id))
                .filter(
                    or_(
                        AuthCredentials.info_status == InfoStatusTypeEnum.PUBLIC.value,
                        and_(
                            AuthCredentials.info_status
                            == InfoStatusTypeEnum.PRIVATE.value,
                            AuthCredentials.user_id == user.id,
                        ),
                    )
                )
                .scalar()
            )

        return {"count": count, "is_filtered": not user.is_superuser}


@app.get("/api/my/credentials")
async def get_my_credentials(request: Request):
    """获取当前用户的私有认证凭据"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    from base import get_db
    from models.auth_model import InfoStatusTypeEnum

    with next(get_db()) as db:
        credentials = (
            db.query(AuthCredentials)
            .filter(
                AuthCredentials.info_status == InfoStatusTypeEnum.PRIVATE.value,
                AuthCredentials.user_id == user.id,
            )
            .all()
        )

        return [
            {
                "id": cred.id,
                "info": cred.info,
                "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
                "created_at": cred.created_at.isoformat() if cred.created_at else None,
                "updated_at": cred.updated_at.isoformat() if cred.updated_at else None,
                "can_edit": True,  # 自己的私有凭据可以编辑
                "can_delete": True,  # 自己的私有凭据可以删除
            }
            for cred in credentials
        ]


@app.get("/api/public/credentials")
async def get_public_credentials(request: Request):
    """获取公开的认证凭据"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    from base import get_db
    from models.auth_model import InfoStatusTypeEnum

    with next(get_db()) as db:
        credentials = (
            db.query(AuthCredentials)
            .filter(AuthCredentials.info_status == InfoStatusTypeEnum.PUBLIC.value)
            .all()
        )

        return [
            {
                "id": cred.id,
                "info": cred.info,
                "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
                "created_at": cred.created_at.isoformat() if cred.created_at else None,
                "updated_at": cred.updated_at.isoformat() if cred.updated_at else None,
                "can_edit": user.is_superuser,  # 只有超级用户可以编辑公开凭据
                "can_delete": user.is_superuser,  # 只有超级用户可以删除公开凭据
            }
            for cred in credentials
        ]


@app.get("/api/permissions/test")
async def test_permissions(request: Request):
    """测试权限系统的API端点"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    from base import get_db

    with next(get_db()) as db:
        # 测试用户查询权限
        if user.is_superuser:
            all_users = db.query(User).all()
            visible_users = len(all_users)
        else:
            visible_users = 1  # 只能看到自己

        # 测试凭据查询权限
        if user.is_superuser:
            all_credentials = db.query(AuthCredentials).all()
            visible_credentials = len(all_credentials)
        else:
            from sqlalchemy import or_, and_
            from models.auth_model import InfoStatusTypeEnum

            filtered_credentials = (
                db.query(AuthCredentials)
                .filter(
                    or_(
                        AuthCredentials.info_status == InfoStatusTypeEnum.PUBLIC.value,
                        and_(
                            AuthCredentials.info_status
                            == InfoStatusTypeEnum.PRIVATE.value,
                            AuthCredentials.user_id == user.id,
                        ),
                    )
                )
                .all()
            )
            visible_credentials = len(filtered_credentials)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
            "permissions": {
                "visible_users": visible_users,
                "visible_credentials": visible_credentials,
                "can_create_users": user.is_superuser,
                "can_create_public_credentials": user.is_superuser,
                "can_edit_all_credentials": user.is_superuser,
            },
            "message": "权限测试完成"
            + (" - 超级用户模式" if user.is_superuser else " - 普通用户模式"),
        }


if __name__ == "__main__":
    import uvicorn

    logger.info("启动完整权限管理应用")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
