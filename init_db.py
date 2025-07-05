"""
数据库初始化脚本
创建表结构并插入示例数据
"""

import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from base import Base, DATABASE_URL
from models.auth_model import User, AuthCredentials, InfoStatusTypeEnum


def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")

    # 创建引擎和会话
    engine = create_engine(DATABASE_URL, echo=True)
    Session = sessionmaker(bind=engine)

    # 删除现有表（如果存在）
    print("删除现有表...")
    Base.metadata.drop_all(engine)
    print("现有表删除完成!")

    # 创建所有表
    print("创建数据库表...")
    Base.metadata.create_all(engine)
    print("数据库表创建完成!")

    # 创建会话并插入示例数据
    session = Session()
    try:
        print("插入示例数据...")

        # 创建示例用户
        users_data = [
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123456",
                "is_active": True,
                "is_superuser": True,
                "remark": "系统管理员账户",
                "description": {
                    "role": "系统管理员",
                    "department": "技术部",
                    "permissions": ["read", "write", "delete", "admin"],
                },
            },
            {
                "username": "user1",
                "email": "user1@example.com",
                "password": "user123456",
                "is_active": True,
                "is_superuser": False,
                "remark": "普通用户账户",
                "description": {
                    "role": "普通用户",
                    "department": "业务部",
                    "permissions": ["read", "write"],
                },
            },
            {
                "username": "user2",
                "email": "user2@example.com",
                "password": "user123456",
                "is_active": True,
                "is_superuser": False,
                "remark": "测试用户账户",
                "description": {
                    "role": "测试用户",
                    "department": "测试部",
                    "permissions": ["read"],
                },
            },
        ]

        created_users = []
        for user_data in users_data:
            user = User(**user_data)
            session.add(user)
            created_users.append(user)
            print(f"创建用户: {user.username}")

        # 提交用户数据以获取ID
        session.commit()

        # 创建示例认证凭据
        credentials_data = [
            {
                "info": "API密钥-生产环境",
                "info_status": InfoStatusTypeEnum.PRIVATE.value,
                "user_id": created_users[0].id,  # admin用户
                "expires_at": datetime.now() + timedelta(days=365),
                "config_info": {
                    "api_url": "https://api.production.example.com",
                    "rate_limit": 1000,
                    "scopes": ["read", "write", "admin"],
                },
                "description": {
                    "purpose": "生产环境API访问",
                    "created_by": "系统管理员",
                    "notes": "用于生产环境的API访问，需要严格保密",
                },
            },
            {
                "info": "数据库连接-开发环境",
                "info_status": InfoStatusTypeEnum.PRIVATE.value,
                "user_id": created_users[1].id,  # user1
                "expires_at": datetime.now() + timedelta(days=90),
                "config_info": {
                    "host": "dev-db.example.com",
                    "port": 5432,
                    "database": "dev_database",
                    "ssl_mode": "require",
                },
                "description": {
                    "purpose": "开发环境数据库访问",
                    "environment": "development",
                    "backup_schedule": "daily",
                },
            },
            {
                "info": "公共API文档访问",
                "info_status": InfoStatusTypeEnum.PUBLIC.value,
                "user_id": None,  # 公开凭据，不关联用户
                "expires_at": None,  # 永不过期
                "config_info": {
                    "doc_url": "https://docs.example.com/api/v1",
                    "version": "1.0",
                    "public_access": True,
                },
                "description": {
                    "purpose": "公共API文档访问",
                    "access_level": "public",
                    "usage": "任何人都可以访问的API文档",
                },
            },
            {
                "info": "第三方服务集成",
                "info_status": InfoStatusTypeEnum.PRIVATE.value,
                "user_id": created_users[0].id,  # admin用户
                "expires_at": datetime.now() + timedelta(days=180),
                "config_info": {
                    "service_name": "OAuth Provider",
                    "client_id": "client_12345",
                    "redirect_uri": "https://app.example.com/callback",
                    "scopes": ["profile", "email"],
                },
                "description": {
                    "purpose": "OAuth第三方登录",
                    "provider": "Google OAuth 2.0",
                    "integration_date": datetime.now().isoformat(),
                },
            },
            {
                "info": "测试环境令牌",
                "info_status": InfoStatusTypeEnum.PUBLIC.value,
                "user_id": None,
                "expires_at": datetime.now() + timedelta(days=30),
                "config_info": {
                    "environment": "testing",
                    "token_type": "bearer",
                    "refresh_available": True,
                },
                "description": {
                    "purpose": "测试环境访问令牌",
                    "restrictions": "仅限测试环境使用",
                    "auto_refresh": True,
                },
            },
        ]

        for cred_data in credentials_data:
            credential = AuthCredentials(**cred_data)
            session.add(credential)
            print(f"创建认证凭据: {credential.info}")

        # 提交所有数据
        session.commit()
        print("示例数据插入完成!")

        # 显示创建的数据摘要
        user_count = session.query(User).count()
        cred_count = session.query(AuthCredentials).count()
        public_cred_count = (
            session.query(AuthCredentials)
            .filter(AuthCredentials.info_status == InfoStatusTypeEnum.PUBLIC.value)
            .count()
        )
        private_cred_count = (
            session.query(AuthCredentials)
            .filter(AuthCredentials.info_status == InfoStatusTypeEnum.PRIVATE.value)
            .count()
        )

        print(f"\n数据库初始化完成!")
        print(f"- 用户数量: {user_count}")
        print(f"- 认证凭据数量: {cred_count}")
        print(f"  - 公开凭据: {public_cred_count}")
        print(f"  - 私有凭据: {private_cred_count}")
        print(f"\n管理员账户:")
        print(f"- 用户名: admin")
        print(f"- 密码: admin123456")
        print(f"- 邮箱: admin@example.com")

    except Exception as e:
        print(f"初始化过程中发生错误: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def reset_database():
    """重置数据库（删除所有表和数据）"""
    print("开始重置数据库...")

    engine = create_engine(DATABASE_URL, echo=True)

    # 删除所有表
    print("删除所有表...")
    Base.metadata.drop_all(engine)
    print("数据库重置完成!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        # 重置数据库
        reset_database()
        print("数据库已重置，可以运行 'python init_db.py' 重新初始化")
    else:
        # 初始化数据库
        init_database()
        print("\n现在可以运行以下命令启动管理系统:")
        print("python main.py")
        print("\n然后在浏览器中访问: http://localhost:8000/admin")
