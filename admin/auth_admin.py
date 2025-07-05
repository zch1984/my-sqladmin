"""
SQLAdmin 管理界面配置
兼容SQLAdmin 0.21.0版本
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from sqladmin import ModelView
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from wtforms import (
    SelectField,
    TextAreaField,
    DateTimeField,
    PasswordField,
    StringField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, Length, Optional as WTFOptional
from wtforms.widgets import PasswordInput, TextArea
import json

from models.auth_model import User, AuthCredentials, InfoStatusTypeEnum


"""
SQLAdmin 管理界面配置
参考官方文档：https://aminalaee.github.io/sqladmin/model_convertors/
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from sqladmin import ModelView
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from wtforms import (
    SelectField,
    TextAreaField,
    DateTimeField,
    PasswordField,
    StringField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, Length, Optional as WTFOptional
from wtforms.widgets import PasswordInput, TextArea
import json

from models.auth_model import User, AuthCredentials, InfoStatusTypeEnum


# JSON字段格式化函数
def format_json_column(data: Any, max_length: int = 100) -> str:
    """格式化JSON数据用于列表显示"""
    if data is None:
        return "无"

    try:
        if isinstance(data, dict):
            # 如果是字典，显示键的数量
            keys = list(data.keys())
            if len(keys) <= 3:
                key_str = ", ".join(f'"{k}"' for k in keys)
                return f"{{{key_str}}}"
            else:
                key_str = ", ".join(f'"{k}"' for k in keys[:2])
                return f"{{{key_str}, ...}} ({len(keys)}个字段)"
        elif isinstance(data, list):
            return f"[数组] ({len(data)}个元素)"
        else:
            # 转换为JSON字符串并截断
            json_str = json.dumps(data, ensure_ascii=False)
            if len(json_str) > max_length:
                return json_str[:max_length] + "..."
            return json_str
    except Exception:
        return (
            str(data)[:max_length] + "..." if len(str(data)) > max_length else str(data)
        )


def format_json_detail(data: Any) -> str:
    """格式化JSON数据用于详情显示"""
    if data is None:
        return "无"

    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        return str(data)


# 自定义JSON字段（参考官方Model Convertors文档）
class CustomJSONField(TextAreaField):
    """自定义JSON字段，支持友好显示和验证"""

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            try:
                # 尝试解析JSON
                if valuelist[0].strip():
                    parsed_data = json.loads(valuelist[0])
                    self.data = parsed_data
                else:
                    self.data = None
            except (json.JSONDecodeError, ValueError) as e:
                # 如果不是有效的JSON，保存原始数据并添加验证错误
                self.data = valuelist[0]
                raise ValidationError(f"无效的JSON格式: {str(e)}")
        else:
            self.data = None

    def _value(self):
        if self.data is not None:
            if isinstance(self.data, str):
                # 如果是字符串，直接返回（可能是验证失败的情况）
                return self.data
            return json.dumps(self.data, ensure_ascii=False, indent=2)
        return ""

    def __call__(self, **kwargs):
        kwargs.setdefault("rows", 8)
        kwargs.setdefault("class_", "form-control json-field")
        kwargs.setdefault(
            "placeholder",
            '请输入有效的JSON格式数据，例如：\n{\n  "key": "value",\n  "number": 123\n}',
        )
        return super().__call__(**kwargs)


# 自定义密码字段
class CustomPasswordField(StringField):
    """自定义密码字段，支持空值不修改现有密码"""

    widget = PasswordInput(hide_value=True)

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = valuelist[0]
        else:
            self.data = None

    def __call__(self, **kwargs):
        kwargs.setdefault("class_", "form-control")
        kwargs.setdefault("placeholder", "输入新密码（留空保持现有密码不变）")
        return super().__call__(**kwargs)


# 信息状态选择字段
class InfoStatusSelectField(SelectField):
    """信息状态选择字段"""

    def __init__(self, *args, **kwargs):
        choices = [
            (InfoStatusTypeEnum.PUBLIC.value, "公开"),
            (InfoStatusTypeEnum.PRIVATE.value, "私有"),
        ]
        kwargs["choices"] = choices
        kwargs["coerce"] = int
        super().__init__(*args, **kwargs)


class UserAdmin(ModelView, model=User):
    """用户管理界面配置"""

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
    column_searchable_list = ["username", "email", "pp_token"]

    # 可排序字段
    column_sortable_list = ["id", "username", "email", "created_at", "updated_at"]

    # 列表页面每页显示数量
    page_size = 20
    page_size_options = [10, 20, 50, 100]

    # 表单配置 - 不包含虚拟字段
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
        "description": CustomJSONField,  # 使用自定义JSON字段
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

    # 列格式化 - 改进JSON字段显示
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

    # 列详情格式化 - 在详情页面中更好地显示JSON
    column_formatters_detail = {
        "description": lambda m, a: format_json_detail(m.description),
        "pp_token": lambda m, a: m.pp_token,
        "created_at": lambda m, a: (
            m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "无"
        ),
        "updated_at": lambda m, a: (
            m.updated_at.strftime("%Y-%m-%d %H:%M:%S") if m.updated_at else "无"
        ),
    }

    # 自定义操作
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True

    async def on_model_change(
        self, data: Dict[str, Any], model: User, is_created: bool, request
    ) -> None:
        """模型变更时的回调"""
        if is_created:
            # 创建时自动生成pp_token
            if not model.pp_token:
                model.pp_token = User.generate_pp_token()

        # 处理密码字段
        if "password" in data and data["password"]:
            # 如果提供了新密码，则加密并保存
            model.hashed_password = User.hash_password(data["password"])

        # 处理JSON字段 - description
        if "description" in data:
            if data["description"]:
                # 数据已经在CustomJSONField中处理过了，直接赋值
                model.description = data["description"]
            else:
                model.description = None

    async def scaffold_form(self, form_class=None):
        """自定义表单构建，添加密码字段"""
        from wtforms import BooleanField

        # 获取基本表单
        FormClass = await super().scaffold_form(form_class)

        # 动态添加密码字段
        class UserForm(FormClass):
            password = CustomPasswordField(
                "密码",
                validators=[WTFOptional(), Length(min=6)],
                description="密码，至少6个字符（留空则不修改现有密码）",
            )

        return UserForm


class AuthCredentialsAdmin(ModelView, model=AuthCredentials):
    """认证凭据管理界面配置"""

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
        "info_status": InfoStatusSelectField,  # 使用自定义选择字段
        "config_info": CustomJSONField,  # 使用自定义JSON字段
        "description": CustomJSONField,  # 使用自定义JSON字段
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

    # 详情页面格式化
    column_formatters_detail = {
        "info_status": lambda m, a: (
            "公开" if m.info_status == InfoStatusTypeEnum.PUBLIC.value else "私有"
        ),
        "user": lambda m, a: m.user.username if m.user else "无关联用户",
        "expires_at": lambda m, a: (
            m.expires_at.strftime("%Y-%m-%d %H:%M:%S") if m.expires_at else "永不过期"
        ),
        "config_info": lambda m, a: format_json_detail(m.config_info),
        "description": lambda m, a: format_json_detail(m.description),
        "created_at": lambda m, a: (
            m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "无"
        ),
        "updated_at": lambda m, a: (
            m.updated_at.strftime("%Y-%m-%d %H:%M:%S") if m.updated_at else "无"
        ),
    }

    # 自定义操作
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True

    async def on_model_change(
        self, data: Dict[str, Any], model: AuthCredentials, is_created: bool, request
    ) -> None:
        """模型变更时的回调"""

        # 处理info_status字段
        if "info_status" in data:
            info_status = data["info_status"]
            if isinstance(info_status, str):
                try:
                    model.info_status = int(info_status)
                except ValueError:
                    model.info_status = InfoStatusTypeEnum.PRIVATE.value

        # 处理JSON字段 - 数据已经在CustomJSONField中处理过了
        for field in ["config_info", "description"]:
            if field in data:
                if data[field]:
                    setattr(model, field, data[field])
                else:
                    setattr(model, field, None)

        # 根据info_status自动设置用户关联
        if hasattr(model, "info_status"):
            if model.info_status == InfoStatusTypeEnum.PUBLIC.value:
                model.user_id = None
            # 私有状态下保持现有的user_id设置


# 自定义仪表板统计
class DashboardStats:
    """仪表板统计数据"""

    @staticmethod
    def get_user_stats(session: Session) -> Dict[str, Any]:
        """获取用户统计"""
        total_users = session.query(func.count(User.id)).scalar()
        active_users = (
            session.query(func.count(User.id)).filter(User.is_active == True).scalar()
        )
        super_users = (
            session.query(func.count(User.id))
            .filter(User.is_superuser == True)
            .scalar()
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "super_users": super_users,
            "inactive_users": total_users - active_users,
        }

    @staticmethod
    def get_credentials_stats(session: Session) -> Dict[str, Any]:
        """获取认证凭据统计"""
        total_credentials = session.query(func.count(AuthCredentials.id)).scalar()
        public_credentials = (
            session.query(func.count(AuthCredentials.id))
            .filter(AuthCredentials.info_status == InfoStatusTypeEnum.PUBLIC.value)
            .scalar()
        )
        private_credentials = (
            session.query(func.count(AuthCredentials.id))
            .filter(AuthCredentials.info_status == InfoStatusTypeEnum.PRIVATE.value)
            .scalar()
        )

        # 过期凭据统计
        now = datetime.now()
        expired_credentials = (
            session.query(func.count(AuthCredentials.id))
            .filter(
                and_(
                    AuthCredentials.expires_at.isnot(None),
                    AuthCredentials.expires_at < now,
                )
            )
            .scalar()
        )

        return {
            "total_credentials": total_credentials,
            "public_credentials": public_credentials,
            "private_credentials": private_credentials,
            "expired_credentials": expired_credentials,
        }
