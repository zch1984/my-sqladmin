"""
SQLAdmin 权限管理 - 强制权限过滤版本
确保权限过滤在所有情况下都能正确工作
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from sqladmin import ModelView
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from wtforms import (
    SelectField,
    TextAreaField,
    DateTimeField,
    PasswordField,
    StringField,
    ValidationError,
    BooleanField,
)
from wtforms.validators import DataRequired, Email, Length, Optional as WTFOptional
from wtforms.widgets import PasswordInput, TextArea
import json
import logging

from models.auth_model import User, AuthCredentials, InfoStatusTypeEnum
from admin.auth_admin import (
    CustomJSONField,
    CustomPasswordField,
    InfoStatusSelectField,
    format_json_column,
    format_json_detail,
)

logger = logging.getLogger(__name__)


class PermissionError(Exception):
    """权限错误异常"""

    def __init__(self, message: str = "权限不足"):
        self.message = message
        super().__init__(self.message)


class ForcedPermissionUserAdmin(ModelView, model=User):
    """强制权限过滤的用户管理界面"""

    # 基本配置
    name = "用户"
    name_plural = "用户管理"
    icon = "fa-solid fa-user"
    category = "用户认证"

    # 列表页面配置
    column_list = [
        "id",
        "username",
        "email",
        "pp_token",
        "is_active",
        "is_superuser",
        "created_at",
        "updated_at",
    ]

    # 列显示名称
    column_labels = {
        "id": "ID",
        "username": "用户名",
        "email": "邮箱",
        "pp_token": "PP令牌",
        "hashed_password": "密码",
        "is_active": "激活状态",
        "is_superuser": "超级管理员",
        "remark": "备注",
        "description": "补充信息",
        "created_at": "创建时间",
        "updated_at": "更新时间",
    }

    # 可搜索字段
    column_searchable_list = ["username", "email"]

    # 可排序字段
    column_sortable_list = ["id", "username", "email", "created_at", "updated_at"]

    # 列表页面每页显示数量
    page_size = 20
    page_size_options = [10, 20, 50, 100]

    # 表单配置
    form_columns = [
        "username",
        "email",
        "is_active",
        "is_superuser",
        "remark",
        "description",
    ]

    # 表单字段配置
    form_args = {
        "username": {
            "validators": [DataRequired(), Length(min=3, max=50)],
            "description": "用户名，3-50个字符",
        },
        "email": {
            "validators": [DataRequired(), Email()],
            "description": "有效的邮箱地址",
        },
        "remark": {"validators": [WTFOptional()], "description": "备注信息"},
        "description": {
            "validators": [WTFOptional()],
            "description": "补充信息（JSON格式）",
        },
    }

    # 表单重写字段类型
    form_overrides = {
        "description": CustomJSONField,
        "remark": TextAreaField,
    }

    # 详情页面配置
    column_details_list = [
        "id",
        "username",
        "email",
        "pp_token",
        "is_active",
        "is_superuser",
        "remark",
        "description",
        "created_at",
        "updated_at",
    ]

    # 列格式化
    column_formatters = {
        "description": lambda m, a: format_json_column(m.description, max_length=80),
        "pp_token": lambda m, a: (
            f"{m.pp_token[:12]}..."
            if m.pp_token and len(m.pp_token) > 12
            else m.pp_token
        ),
        "created_at": lambda m, a: (
            m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "无"
        ),
        "updated_at": lambda m, a: (
            m.updated_at.strftime("%Y-%m-%d %H:%M:%S") if m.updated_at else "无"
        ),
    }

    # 权限控制
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True

    def get_current_user(self, request: Request) -> Optional[User]:
        """获取当前登录用户"""
        return getattr(request.state, "user", None)

    def is_superuser(self, request: Request) -> bool:
        """检查是否为超级用户"""
        user = self.get_current_user(request)
        return user and user.is_superuser

    # 多种方法确保权限过滤生效
    def get_list_query(self, request: Request = None):
        """权限过滤查询方法1"""
        if request is None:
            # 如果没有请求对象，返回空查询
            return self.sessionmaker().query(self.model).filter(False)

        current_user = self.get_current_user(request)
        logger.info(
            f"get_list_query - 当前用户: {current_user.username if current_user else 'None'}"
        )

        if not current_user:
            logger.warning("用户未登录，返回空查询")
            return self.sessionmaker().query(self.model).filter(False)

        query = self.sessionmaker().query(self.model)

        if current_user.is_superuser:
            logger.info(f"超级用户 {current_user.username} 查看所有用户")
            return query
        else:
            logger.info(f"普通用户 {current_user.username} 只能查看自己")
            filtered_query = query.filter(User.id == current_user.id)
            return filtered_query

    def get_query(self, request: Request = None):
        """权限过滤查询方法2"""
        return self.get_list_query(request)

    def count_query(self, request: Request = None):
        """计数查询也要应用权限过滤"""
        if request is None:
            return self.sessionmaker().query(func.count(self.model.id)).filter(False)

        return self.get_list_query(request).with_entities(func.count(self.model.id))

    async def list(self, request: Request) -> Response:
        """重写列表方法"""
        current_user = self.get_current_user(request)
        logger.info(
            f"list 方法 - 当前用户: {current_user.username if current_user else 'None'}"
        )

        if not current_user:
            raise PermissionError("用户未登录")

        return await super().list(request)

    async def create(self, request: Request) -> Response:
        """创建用户权限检查"""
        current_user = self.get_current_user(request)

        if not current_user or not current_user.is_superuser:
            raise PermissionError("只有超级管理员可以创建用户")

        return await super().create(request)

    async def edit(self, request: Request) -> Response:
        """编辑用户权限检查"""
        current_user = self.get_current_user(request)
        user_id = request.path_params.get("pk")

        if not current_user:
            raise PermissionError("用户未登录")

        if current_user.is_superuser:
            return await super().edit(request)
        else:
            if user_id and int(user_id) == current_user.id:
                return await super().edit(request)
            else:
                raise PermissionError("只能编辑自己的信息")

    async def delete(self, request: Request) -> Response:
        """删除用户权限检查"""
        current_user = self.get_current_user(request)

        if not current_user or not current_user.is_superuser:
            raise PermissionError("只有超级管理员可以删除用户")

        return await super().delete(request)

    async def details(self, request: Request) -> Response:
        """查看详情权限检查"""
        current_user = self.get_current_user(request)
        user_id = request.path_params.get("pk")

        if not current_user:
            raise PermissionError("用户未登录")

        if current_user.is_superuser:
            return await super().details(request)
        else:
            if user_id and int(user_id) == current_user.id:
                return await super().details(request)
            else:
                raise PermissionError("只能查看自己的信息")

    async def scaffold_form(self, form_class=None):
        """构建表单"""
        FormClass = await super().scaffold_form(form_class)

        class UserForm(FormClass):
            password = CustomPasswordField(
                "密码",
                validators=[WTFOptional(), Length(min=6)],
                description="密码，至少6个字符（留空则不修改现有密码）",
            )

        return UserForm

    async def on_model_change(
        self, data: Dict[str, Any], model: User, is_created: bool, request: Request
    ) -> None:
        """模型变更回调"""
        current_user = self.get_current_user(request)

        if not current_user:
            raise PermissionError("用户未登录")

        # 权限检查
        if is_created and not current_user.is_superuser:
            raise PermissionError("只有超级管理员可以创建用户")

        if not is_created:
            if not current_user.is_superuser and current_user.id != model.id:
                raise PermissionError("只能修改自己的信息")

            # 普通用户字段限制
            if not current_user.is_superuser:
                forbidden_fields = ["pp_token", "is_superuser", "is_active"]
                for field in forbidden_fields:
                    if field in data:
                        raise PermissionError(f"无权修改字段: {field}")

        # 处理密码
        if "password" in data and data["password"]:
            model.hashed_password = User.hash_password(data["password"])

        # 处理JSON字段
        if "description" in data:
            model.description = data["description"] if data["description"] else None

        # 创建时生成pp_token
        if is_created and not model.pp_token:
            model.pp_token = User.generate_pp_token()


class ForcedPermissionCredentialsAdmin(ModelView, model=AuthCredentials):
    """强制权限过滤的认证凭据管理界面"""

    # 基本配置
    name = "认证凭据"
    name_plural = "认证凭据管理"
    icon = "fa-solid fa-key"
    category = "用户认证"

    # 列表页面配置
    column_list = [
        "id",
        "info",
        "info_status",
        "user",
        "expires_at",
        "created_at",
        "updated_at",
    ]

    # 列显示名称
    column_labels = {
        "id": "ID",
        "info": "认证信息",
        "info_status": "信息状态",
        "config_info": "配置信息",
        "description": "补充信息",
        "expires_at": "过期时间",
        "user_id": "用户ID",
        "user": "关联用户",
        "created_at": "创建时间",
        "updated_at": "更新时间",
    }

    # 可搜索字段
    column_searchable_list = ["info"]

    # 可排序字段
    column_sortable_list = [
        "id",
        "info",
        "info_status",
        "expires_at",
        "created_at",
        "updated_at",
    ]

    # 列表页面每页显示数量
    page_size = 20
    page_size_options = [10, 20, 50, 100]

    # 表单配置
    form_columns = [
        "info",
        "info_status",
        "user_id",
        "expires_at",
        "config_info",
        "description",
    ]

    # 表单字段配置
    form_args = {
        "info": {
            "validators": [WTFOptional(), Length(max=100)],
            "description": "认证信息，最多100个字符",
        },
        "info_status": {"description": "信息状态：0-公开，1-私有"},
        "user_id": {"description": "关联的用户ID（私有状态时需要）"},
        "expires_at": {
            "validators": [WTFOptional()],
            "description": "凭据过期时间（可选）",
        },
        "config_info": {
            "validators": [WTFOptional()],
            "description": "配置信息（JSON格式）",
        },
        "description": {
            "validators": [WTFOptional()],
            "description": "补充信息（JSON格式）",
        },
    }

    # 表单重写字段类型
    form_overrides = {
        "info_status": InfoStatusSelectField,
        "config_info": CustomJSONField,
        "description": CustomJSONField,
        "expires_at": DateTimeField,
    }

    # 详情页面配置
    column_details_list = [
        "id",
        "info",
        "info_status",
        "user",
        "expires_at",
        "config_info",
        "description",
        "created_at",
        "updated_at",
    ]

    # 列格式化
    column_formatters = {
        "info_status": lambda m, a: (
            "公开" if m.info_status == InfoStatusTypeEnum.PUBLIC.value else "私有"
        ),
        "user": lambda m, a: m.user.username if m.user else "无关联用户",
        "expires_at": lambda m, a: (
            m.expires_at.strftime("%Y-%m-%d %H:%M:%S") if m.expires_at else "永不过期"
        ),
        "config_info": lambda m, a: format_json_column(m.config_info, max_length=50),
        "description": lambda m, a: format_json_column(m.description, max_length=50),
        "created_at": lambda m, a: (
            m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "无"
        ),
        "updated_at": lambda m, a: (
            m.updated_at.strftime("%Y-%m-%d %H:%M:%S") if m.updated_at else "无"
        ),
    }

    # 权限控制
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True

    def get_current_user(self, request: Request) -> Optional[User]:
        """获取当前登录用户"""
        return getattr(request.state, "user", None)

    def is_superuser(self, request: Request) -> bool:
        """检查是否为超级用户"""
        user = self.get_current_user(request)
        return user and user.is_superuser

    # 多种方法确保权限过滤生效
    def get_list_query(self, request: Request = None):
        """权限过滤查询方法1"""
        if request is None:
            # 如果没有请求对象，返回空查询
            return self.sessionmaker().query(self.model).filter(False)

        current_user = self.get_current_user(request)
        logger.info(
            f"Credentials get_list_query - 当前用户: {current_user.username if current_user else 'None'}"
        )

        if not current_user:
            logger.warning("用户未登录，返回空查询")
            return self.sessionmaker().query(self.model).filter(False)

        query = self.sessionmaker().query(self.model)

        if current_user.is_superuser:
            logger.info(f"超级用户 {current_user.username} 查看所有认证凭据")
            return query
        else:
            logger.info(
                f"普通用户 {current_user.username} - 只能查看公开凭据和自己的私有凭据"
            )
            filtered_query = query.filter(
                or_(
                    # 公开凭据 (info_status=0) - 可查看但不能编辑
                    AuthCredentials.info_status == InfoStatusTypeEnum.PUBLIC.value,
                    # 自己的私有凭据 (info_status=1 且 user_id=自己) - 可查看和编辑
                    and_(
                        AuthCredentials.info_status == InfoStatusTypeEnum.PRIVATE.value,
                        AuthCredentials.user_id == current_user.id,
                    ),
                )
            )
            return filtered_query

    def get_query(self, request: Request = None):
        """权限过滤查询方法2"""
        return self.get_list_query(request)

    def count_query(self, request: Request = None):
        """计数查询也要应用权限过滤"""
        if request is None:
            return self.sessionmaker().query(func.count(self.model.id)).filter(False)

        return self.get_list_query(request).with_entities(func.count(self.model.id))

    async def list(self, request: Request) -> Response:
        """重写列表方法"""
        current_user = self.get_current_user(request)
        logger.info(
            f"Credentials list 方法 - 当前用户: {current_user.username if current_user else 'None'}"
        )

        if not current_user:
            raise PermissionError("用户未登录")

        return await super().list(request)

    async def create(self, request: Request) -> Response:
        """创建认证凭据"""
        current_user = self.get_current_user(request)

        if not current_user:
            raise PermissionError("用户未登录")

        return await super().create(request)

    async def edit(self, request: Request) -> Response:
        """编辑认证凭据权限检查"""
        current_user = self.get_current_user(request)
        credential_id = request.path_params.get("pk")

        if not current_user:
            raise PermissionError("用户未登录")

        if current_user.is_superuser:
            return await super().edit(request)
        else:
            # 普通用户只能编辑自己的私有凭据
            if credential_id:
                with self.sessionmaker() as session:
                    credential = session.get(AuthCredentials, int(credential_id))
                    if (
                        credential
                        and credential.info_status == InfoStatusTypeEnum.PRIVATE.value
                        and credential.user_id == current_user.id
                    ):
                        return await super().edit(request)
                    else:
                        raise PermissionError("只能编辑自己的私有认证凭据")
            else:
                raise PermissionError("凭据不存在")

    async def delete(self, request: Request) -> Response:
        """删除认证凭据权限检查"""
        current_user = self.get_current_user(request)
        credential_id = request.path_params.get("pk")

        if not current_user:
            raise PermissionError("用户未登录")

        if current_user.is_superuser:
            return await super().delete(request)
        else:
            # 普通用户只能删除自己的私有凭据
            if credential_id:
                with self.sessionmaker() as session:
                    credential = session.get(AuthCredentials, int(credential_id))
                    if (
                        credential
                        and credential.info_status == InfoStatusTypeEnum.PRIVATE.value
                        and credential.user_id == current_user.id
                    ):
                        return await super().delete(request)
                    else:
                        raise PermissionError("只能删除自己的私有认证凭据")
            else:
                raise PermissionError("凭据不存在")

    async def details(self, request: Request) -> Response:
        """查看详情权限检查"""
        current_user = self.get_current_user(request)
        credential_id = request.path_params.get("pk")

        if not current_user:
            raise PermissionError("用户未登录")

        if current_user.is_superuser:
            return await super().details(request)
        else:
            # 普通用户可以查看公开凭据和自己的私有凭据
            if credential_id:
                with self.sessionmaker() as session:
                    credential = session.get(AuthCredentials, int(credential_id))
                    if credential and (
                        credential.info_status == InfoStatusTypeEnum.PUBLIC.value
                        or (
                            credential.info_status == InfoStatusTypeEnum.PRIVATE.value
                            and credential.user_id == current_user.id
                        )
                    ):
                        return await super().details(request)
                    else:
                        raise PermissionError("无权查看该认证凭据")
            else:
                raise PermissionError("凭据不存在")

    async def on_model_change(
        self,
        data: Dict[str, Any],
        model: AuthCredentials,
        is_created: bool,
        request: Request,
    ) -> None:
        """模型变更回调"""
        current_user = self.get_current_user(request)

        if not current_user:
            raise PermissionError("用户未登录")

        # 权限检查
        if not is_created:
            if not current_user.is_superuser:
                # 普通用户只能修改自己的私有凭据
                if not (
                    model.info_status == InfoStatusTypeEnum.PRIVATE.value
                    and model.user_id == current_user.id
                ):
                    raise PermissionError("只能修改自己的私有认证凭据")

        # 处理info_status字段
        if "info_status" in data:
            info_status = data["info_status"]
            if isinstance(info_status, str):
                try:
                    model.info_status = int(info_status)
                except ValueError:
                    model.info_status = InfoStatusTypeEnum.PRIVATE.value

        # 处理JSON字段
        for field in ["config_info", "description"]:
            if field in data:
                setattr(model, field, data[field] if data[field] else None)

        # 创建时的特殊处理
        if is_created:
            if not current_user.is_superuser:
                # 普通用户创建的凭据自动设为私有并关联到自己
                model.info_status = InfoStatusTypeEnum.PRIVATE.value
                model.user_id = current_user.id
                logger.info(f"普通用户 {current_user.username} 创建私有凭据")
            else:
                # 超级用户创建时，根据info_status设置用户关联
                if model.info_status == InfoStatusTypeEnum.PUBLIC.value:
                    model.user_id = None
                    logger.info(f"超级用户 {current_user.username} 创建公开凭据")
                elif "user_id" not in data or not data["user_id"]:
                    # 如果是私有状态但没有指定用户，关联到当前用户
                    model.user_id = current_user.id
                    logger.info(f"超级用户 {current_user.username} 创建私有凭据")


# 导出类
__all__ = [
    "ForcedPermissionUserAdmin",
    "ForcedPermissionCredentialsAdmin",
    "PermissionError",
]
