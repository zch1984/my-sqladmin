"""
SQLAdmin 权限管理完整实现
基于用户角色的细粒度权限控制
参考 SQLAdmin 官方文档的最佳实践
"""

from typing import Any, Dict, Optional
from sqladmin import ModelView
from sqlalchemy import func, and_, or_
from starlette.requests import Request
from starlette.responses import Response
from wtforms import (
    TextAreaField,
    DateTimeField,
)
from wtforms.validators import DataRequired, Email, Length, Optional as WTFOptional
import logging

from models.auth_model import User, AuthCredentials, InfoStatusTypeEnum
from forms.auth_forms import (
    CustomJSONField,
    CustomPasswordField,
    InfoStatusSelectField,
    format_json_column,
)

logger = logging.getLogger(__name__)


class PermissionError(Exception):
    """权限错误异常"""

    def __init__(self, message: str = "权限不足"):
        self.message = message
        super().__init__(self.message)


class BasePermissionAdmin(ModelView):
    """基础权限管理类"""

    def _get_session(self):
        """获取数据库会话 - SQLAdmin的标准方式"""
        from base import SessionLocal

        return SessionLocal()

    def get_current_user(self, request: Request) -> Optional[User]:
        """获取当前登录用户"""
        return getattr(request.state, "user", None)

    def is_superuser(self, request: Request) -> bool:
        """检查是否为超级用户"""
        user = self.get_current_user(request)
        return user and user.is_superuser

    async def check_permissions(self, request: Request, action: str = "view") -> bool:
        """检查权限 - 子类需要重写"""
        return True


class UserPermissionAdmin(BasePermissionAdmin, model=User):
    """用户权限管理界面"""

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

    # 表单配置 - 静态设置（动态控制在运行时处理）
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

    # 权限控制属性 - 动态设置
    @property
    def can_create(self) -> bool:
        """只有超级用户可以创建用户"""
        return True  # 在具体操作中检查

    @property
    def can_edit(self) -> bool:
        """根据权限决定是否可以编辑"""
        return True  # 在具体操作中检查

    @property
    def can_delete(self) -> bool:
        """只有超级用户可以删除用户"""
        return True  # 在具体操作中检查

    @property
    def can_view_details(self) -> bool:
        """可以查看详情"""
        return True

    # 重写查询方法 - 核心权限过滤（使用SQLAdmin的正确方法名）
    def list_query(self, request: Request):
        """根据用户权限过滤用户列表"""
        current_user = self.get_current_user(request)
        logger.info(
            f"UserAdmin list_query 被调用 - 当前用户: {current_user.username if current_user else 'None'}"
        )

        # 使用 SQLAdmin 的标准会话获取方式
        session = self._get_session()
        query = session.query(self.model)

        if not current_user:
            # 未登录用户返回空查询
            logger.warning("用户未登录，返回空查询")
            return query.filter(False)

        if current_user.is_superuser:
            # 超级用户可以看到所有用户
            logger.info(f"超级用户 {current_user.username} 查看所有用户")
            return query
        else:
            # 普通用户只能看到自己
            logger.info(f"普通用户 {current_user.username} 只能查看自己的信息")
            return query.filter(User.id == current_user.id)

    async def list(self, request: Request) -> Response:
        """重写列表方法，确保权限过滤"""
        current_user = self.get_current_user(request)
        logger.info(
            f"UserAdmin list 方法被调用 - 当前用户: {current_user.username if current_user else 'None'}"
        )

        if not current_user:
            raise PermissionError("用户未登录")

        return await super().list(request)

    def count_query(self, request: Request):
        """计数查询，也需要应用权限过滤"""
        current_user = self.get_current_user(request)
        logger.info(
            f"UserAdmin count_query - 当前用户: {current_user.username if current_user else 'None'}"
        )

        session = self._get_session()
        query = session.query(func.count(self.model.id))

        if not current_user:
            logger.warning("用户未登录，返回 0")
            return query.filter(False)

        if current_user.is_superuser:
            logger.info("超级用户 - 返回所有用户的计数查询")
            return query
        else:
            # 普通用户只能看到自己
            logger.info(f"普通用户 - 返回自己的计数查询，用户ID: {current_user.id}")
            return query.filter(User.id == current_user.id)

    def details_query(self, request: Request):
        """详情查询，应用权限过滤"""
        return self.list_query(request)

    def get_one(self, id: Any, request: Request):
        """获取单个用户 - 权限检查"""
        current_user = self.get_current_user(request)

        if not current_user:
            return None

        session = self._get_session()
        query = session.query(self.model)

        if current_user.is_superuser:
            # 超级用户可以查看任何用户
            return query.filter(self.model.id == id).first()
        else:
            # 普通用户只能查看自己
            if int(id) == current_user.id:
                return query.filter(self.model.id == id).first()
            else:
                return None

    # 重写操作方法
    async def create(self, request: Request) -> Response:
        """创建用户 - 权限检查"""
        current_user = self.get_current_user(request)

        if not current_user or not current_user.is_superuser:
            raise PermissionError("只有超级管理员可以创建用户")

        return await super().create(request)

    async def edit(self, request: Request) -> Response:
        """编辑用户 - 权限检查"""
        current_user = self.get_current_user(request)
        user_id = request.path_params.get("pk")

        if not current_user:
            raise PermissionError("用户未登录")

        if not current_user.is_superuser:
            # 普通用户只能编辑自己
            if not (user_id and int(user_id) == current_user.id):
                raise PermissionError("只能编辑自己的信息")

        return await super().edit(request)

    async def delete(self, request: Request) -> Response:
        """删除用户 - 权限检查"""
        current_user = self.get_current_user(request)

        if not current_user or not current_user.is_superuser:
            raise PermissionError("只有超级管理员可以删除用户")

        return await super().delete(request)

    # 动态表单字段控制 - 通过scaffold_form实现
    async def scaffold_form(self, form_class=None):
        """构建表单，根据权限动态调整字段和添加密码字段"""
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
        """模型变更时的回调 - 权限和字段检查"""
        current_user = self.get_current_user(request)

        if not current_user:
            raise PermissionError("用户未登录")

        # 权限检查
        if is_created and not current_user.is_superuser:
            raise PermissionError("只有超级管理员可以创建用户")

        if not is_created:
            # 编辑时权限检查
            if not current_user.is_superuser and current_user.id != model.id:
                raise PermissionError("只能修改自己的信息")

            # 普通用户字段限制检查
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


class CredentialsPermissionAdmin(BasePermissionAdmin, model=AuthCredentials):
    """认证凭据权限管理界面"""

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

    # 表单配置 - 静态设置（动态控制在运行时处理）
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

    # 权限控制属性 - 动态设置
    @property
    def can_create(self) -> bool:
        """根据权限决定是否可以创建"""
        return True  # 在具体操作中检查

    @property
    def can_edit(self) -> bool:
        """根据权限决定是否可以编辑"""
        return True  # 在具体操作中检查

    @property
    def can_delete(self) -> bool:
        """根据权限决定是否可以删除"""
        return True  # 在具体操作中检查

    @property
    def can_view_details(self) -> bool:
        """可以查看详情"""
        return True

    # 重写查询方法 - 核心权限过滤（使用SQLAdmin的正确方法名）
    def list_query(self, request: Request):
        """根据用户权限过滤认证凭据列表"""
        current_user = self.get_current_user(request)

        logger.info(
            f"CredentialsAdmin list_query 被调用 - 当前用户: {current_user.username if current_user else 'None'}"
        )

        session = self._get_session()
        query = session.query(self.model)

        if not current_user:
            # 未登录用户返回空查询
            logger.warning("用户未登录，返回空查询")
            return query.filter(False)

        if current_user.is_superuser:
            # 超级用户可以看到所有凭据
            logger.info(f"超级用户 {current_user.username} 查看所有认证凭据")
            return query
        else:
            # 普通用户只能看到：
            # 1. 公开的凭据（info_status=0）
            # 2. 自己关联的私有凭据（info_status=1 且 user_id=当前用户）
            logger.info(f"普通用户 {current_user.username} 查看受限的认证凭据")
            return query.filter(
                or_(
                    # 公开凭据 - 可查看但不能编辑
                    AuthCredentials.info_status == InfoStatusTypeEnum.PUBLIC.value,
                    # 自己的私有凭据 - 可查看和编辑
                    and_(
                        AuthCredentials.info_status == InfoStatusTypeEnum.PRIVATE.value,
                        AuthCredentials.user_id == current_user.id,
                    ),
                )
            )

    async def list(self, request: Request) -> Response:
        """重写列表方法，确保权限过滤"""
        current_user = self.get_current_user(request)
        logger.info(
            f"CredentialsAdmin list 方法被调用 - 当前用户: {current_user.username if current_user else 'None'}"
        )

        if not current_user:
            raise PermissionError("用户未登录")

        return await super().list(request)

    def count_query(self, request: Request):
        """计数查询，也需要应用权限过滤"""
        current_user = self.get_current_user(request)
        logger.info(
            f"CredentialsAdmin count_query - 当前用户: {current_user.username if current_user else 'None'}"
        )

        session = self._get_session()
        query = session.query(func.count(self.model.id))

        if not current_user:
            logger.warning("用户未登录，返回 0")
            return query.filter(False)

        if current_user.is_superuser:
            # 超级用户可以看到所有凭据
            logger.info("超级用户 - 返回所有凭据的计数查询")
            return query
        else:
            # 普通用户只能看到自己的私有凭据和所有公开凭据
            return query.filter(
                or_(
                    # 公开凭据
                    AuthCredentials.info_status == InfoStatusTypeEnum.PUBLIC.value,
                    # 自己的私有凭据
                    and_(
                        AuthCredentials.info_status == InfoStatusTypeEnum.PRIVATE.value,
                        AuthCredentials.user_id == current_user.id,
                    ),
                )
            )

    def details_query(self, request: Request):
        """详情查询，应用权限过滤"""
        return self.list_query(request)

    def get_one(self, id: Any, request: Request):
        """获取单个认证凭据 - 权限检查"""
        current_user = self.get_current_user(request)

        if not current_user:
            return None

        session = self._get_session()
        query = session.query(self.model)
        credential = query.filter(self.model.id == id).first()

        if not credential:
            return None

        if current_user.is_superuser:
            # 超级用户可以查看任何凭据
            return credential
        else:
            # 普通用户只能查看公开凭据或自己的私有凭据
            if credential.info_status == InfoStatusTypeEnum.PUBLIC.value or (
                credential.info_status == InfoStatusTypeEnum.PRIVATE.value
                and credential.user_id == current_user.id
            ):
                return credential
            else:
                return None

    # 重写操作方法
    async def create(self, request: Request) -> Response:
        """创建认证凭据 - 权限检查"""
        current_user = self.get_current_user(request)

        if not current_user:
            raise PermissionError("用户未登录")

        # 所有用户都可以创建凭据，但普通用户只能创建私有凭据
        return await super().create(request)

    async def edit(self, request: Request) -> Response:
        """编辑认证凭据 - 权限检查"""
        current_user = self.get_current_user(request)
        credential_id = request.path_params.get("pk")

        if not current_user:
            raise PermissionError("用户未登录")

        session = self._get_session()

        if current_user.is_superuser:
            # 超级用户可以编辑任何凭据
            return await super().edit(request)
        else:
            # 普通用户只能编辑自己的私有凭据
            if credential_id:
                # 这里需要用 session 查询，而不是 get_one，避免循环调用
                credential = (
                    session.query(self.model)
                    .filter(self.model.id == credential_id)
                    .first()
                )
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
        """删除认证凭据 - 权限检查"""
        current_user = self.get_current_user(request)
        credential_id = request.path_params.get("pk")

        if not current_user:
            raise PermissionError("用户未登录")

        session = self._get_session()

        if current_user.is_superuser:
            # 超级用户可以删除任何凭据
            return await super().delete(request)
        else:
            # 普通用户只能删除自己的私有凭据
            if credential_id:
                # 这里需要用 session 查询，而不是 get_one，避免循环调用
                credential = (
                    session.query(self.model)
                    .filter(self.model.id == credential_id)
                    .first()
                )
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

    # 在权限检查和数据处理中实现字段控制

    async def on_model_change(
        self,
        data: Dict[str, Any],
        model: AuthCredentials,
        is_created: bool,
        request: Request,
    ) -> None:
        """模型变更时的回调 - 权限和字段检查"""
        current_user = self.get_current_user(request)

        if not current_user:
            raise PermissionError("用户未登录")

        # 权限检查
        if not is_created:
            # 编辑时权限检查
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
            else:
                # 超级用户创建时，根据info_status设置用户关联
                if model.info_status == InfoStatusTypeEnum.PUBLIC.value:
                    model.user_id = None
                elif "user_id" not in data or not data["user_id"]:
                    # 如果是私有状态但没有指定用户，关联到当前用户
                    model.user_id = current_user.id


# 导出类
__all__ = [
    "UserPermissionAdmin",
    "CredentialsPermissionAdmin",
    "PermissionError",
]
