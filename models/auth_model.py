"""
认证管理数据模型 - SQLAlchemy 2.0 风格
"""

import uuid
import bcrypt
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum

from base import Base


class AuthStatusEnum(str, Enum):
    """认证状态枚举"""

    PENDING = "pending"  # 待认证
    APPROVED = "approved"  # 已认证
    REJECTED = "rejected"  # 已拒绝
    SUSPENDED = "suspended"  # 已暂停


class CredentialTypeEnum(str, Enum):
    """凭据类型枚举"""

    PASSWORD = "password"  # 密码
    API_KEY = "api_key"  # API密钥
    TOKEN = "token"  # 令牌
    CERTIFICATE = "certificate"  # 证书


class InfoStatusTypeEnum(int, Enum):
    """信息状态枚举"""

    PUBLIC = 0  # 公开
    PRIVATE = 1  # 私有


# FastAdmin需要的用户模型
class User(Base):
    """用户表 - FastAdmin管理员用户"""

    __tablename__ = "users"

    # 使用 UUID 主键
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    pp_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="PP平台token",
        default=lambda: str(uuid.uuid4()),
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, default="default_password"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否超级管理员"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="备注信息"
    )
    description: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="补充信息"
    )  # 使用JSONB类型存储结构化描述
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now().replace(tzinfo=None),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now().replace(tzinfo=None),
        onupdate=lambda: datetime.now().replace(tzinfo=None),
        comment="更新时间",
    )

    def __init__(self, **kwargs):
        """初始化用户，自动生成pp_token"""
        if "pp_token" not in kwargs or not kwargs["pp_token"]:
            kwargs["pp_token"] = self.generate_pp_token()
        super().__init__(**kwargs)

    @staticmethod
    def generate_pp_token() -> str:
        """生成PP平台token"""
        return f"pp_{uuid.uuid4().hex[:16]}"

    # 添加虚拟密码属性供 SQLAdmin 使用
    @property
    def password(self):
        """密码属性（用于表单显示）"""
        return ""  # 永远不返回实际密码

    @password.setter
    def password(self, value):
        """设置密码时自动加密"""
        if value:
            self.hashed_password = self.hash_password(value)

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.hashed_password.encode("utf-8")
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def __str__(self):
        return self.username


class AuthCredentials(Base):
    """认证凭据表"""

    __tablename__ = "auth_credentials"

    # 使用 SQLAlchemy 2.0 风格的类型注解
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    info: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="认证信息"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="过期时间"
    )
    # 信息状态字段：0-公开(public)，1-个人(single)
    info_status: Mapped[InfoStatusTypeEnum] = mapped_column(
        Integer,
        default=InfoStatusTypeEnum.PRIVATE.value,
        nullable=False,
        comment="信息状态: 0-公开(public), 1-个人(single)",
    )
    config_info: Mapped[Optional[str]] = mapped_column(
        JSONB, nullable=True, comment="配置信息"
    )
    description: Mapped[Optional[str]] = mapped_column(
        JSONB, nullable=True, comment="补充信息"
    )  # 修正为字符串类型
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now().replace(tzinfo=None)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now().replace(tzinfo=None),
        onupdate=lambda: datetime.now().replace(tzinfo=None),
    )

    # 关联用户 - 使用整数外键
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", backref="auth_managements", lazy="joined"
    )

    def __init__(self, **kwargs):
        """初始化认证凭据，根据info_status自动设置用户关联"""
        # 处理info_status的类型转换
        if "info_status" in kwargs:
            info_status = kwargs["info_status"]
            if isinstance(info_status, str):
                # 如果是字符串，尝试转换为枚举
                if info_status.upper() == "PUBLIC":
                    kwargs["info_status"] = InfoStatusTypeEnum.PUBLIC.value
                elif info_status.upper() == "PRIVATE":
                    kwargs["info_status"] = InfoStatusTypeEnum.PRIVATE.value
                else:
                    # 如果是数字字符串，转换为整数
                    try:
                        kwargs["info_status"] = int(info_status)
                    except ValueError:
                        kwargs["info_status"] = InfoStatusTypeEnum.PRIVATE.value
            elif isinstance(info_status, InfoStatusTypeEnum):
                kwargs["info_status"] = info_status.value
            elif not isinstance(info_status, int):
                kwargs["info_status"] = InfoStatusTypeEnum.PRIVATE.value

        # 处理时区问题 - 确保 expires_at 没有时区信息
        if "expires_at" in kwargs and kwargs["expires_at"] is not None:
            expires_at = kwargs["expires_at"]
            if isinstance(expires_at, datetime) and expires_at.tzinfo is not None:
                # 如果有时区信息，转换为UTC时间并移除时区信息
                kwargs["expires_at"] = expires_at.astimezone(timezone.utc).replace(
                    tzinfo=None
                )

        # 如果设置了info_status，根据其值决定用户关联
        if "info_status" in kwargs:
            info_status_value = kwargs["info_status"]

            # 如果是公开状态(0)，清除用户关联
            if info_status_value == InfoStatusTypeEnum.PUBLIC.value:
                kwargs["user_id"] = None
            # 如果是私有状态(1)，需要通过外部设置current_user_id
            elif info_status_value == InfoStatusTypeEnum.PRIVATE.value:
                # 这里需要从外部传入当前用户ID
                if "current_user_id" in kwargs:
                    kwargs["user_id"] = kwargs.pop("current_user_id")
                elif "user_id" not in kwargs:
                    # 如果没有提供用户ID，保持为None（需要在业务逻辑中处理）
                    kwargs["user_id"] = None

        super().__init__(**kwargs)

    @property
    def info_status_enum(self) -> InfoStatusTypeEnum:
        """获取info_status的枚举值"""
        try:
            if isinstance(self.info_status, int):
                return InfoStatusTypeEnum(self.info_status)
            elif isinstance(self.info_status, str):
                if self.info_status.upper() == "PUBLIC":
                    return InfoStatusTypeEnum.PUBLIC
                elif self.info_status.upper() == "PRIVATE":
                    return InfoStatusTypeEnum.PRIVATE
                else:
                    return InfoStatusTypeEnum(int(self.info_status))
            else:
                return InfoStatusTypeEnum.PRIVATE
        except (ValueError, TypeError):
            return InfoStatusTypeEnum.PRIVATE

    def set_user_based_on_status(self, current_user_id: Optional[int] = None):
        """根据info_status设置用户关联"""
        if self.info_status == InfoStatusTypeEnum.PUBLIC:
            # 公开状态，清除用户关联
            self.user_id = None
        elif self.info_status == InfoStatusTypeEnum.PRIVATE:
            # 私有状态，设置为当前用户
            if current_user_id:
                self.user_id = current_user_id

    def __str__(self):
        return f"{self.info}"
