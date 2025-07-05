"""
创建初始管理员用户
"""

from base import get_db
from models.auth_model import User


def create_admin_user():
    """创建初始管理员用户"""
    with next(get_db()) as db:
        # 检查是否已存在管理员用户
        admin_user = (
            db.query(User)
            .filter(User.username == "admin", User.is_superuser == True)
            .first()
        )

        if admin_user:
            print("管理员用户已存在")
            print(f"用户名: {admin_user.username}")
            print(f"邮箱: {admin_user.email}")
            return admin_user

        # 创建新的管理员用户
        admin_user = User(
            username="admin",
            email="admin@example.com",
            is_active=True,
            is_superuser=True,
            remark="系统初始管理员用户",
            description={
                "role": "系统管理员",
                "permissions": ["all"],
                "created_by": "system",
            },
        )

        # 设置默认密码
        admin_user.hashed_password = User.hash_password("admin123")

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ 管理员用户创建成功！")
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email}")
        print(f"密码: admin123")
        print(f"PP令牌: {admin_user.pp_token}")
        print("⚠️  请在生产环境中修改默认密码！")

        return admin_user


def create_test_users():
    """创建测试用户"""
    with next(get_db()) as db:
        test_users = [
            {
                "username": "testuser",
                "email": "test@example.com",
                "is_superuser": False,
                "remark": "测试普通用户",
                "description": {"role": "普通用户", "department": "测试部门"},
            },
            {
                "username": "manager",
                "email": "manager@example.com",
                "is_superuser": True,
                "remark": "测试管理员用户",
                "description": {"role": "部门管理员", "department": "管理部门"},
            },
        ]

        for user_data in test_users:
            existing_user = (
                db.query(User).filter(User.username == user_data["username"]).first()
            )

            if not existing_user:
                user = User(**user_data)
                user.hashed_password = User.hash_password("password123")
                db.add(user)
                print(f"✅ 创建测试用户: {user_data['username']}")

        db.commit()


if __name__ == "__main__":
    print("🚀 初始化SQLAdmin管理用户...")
    create_admin_user()
    print("\n📝 创建测试用户...")
    create_test_users()
    print("\n🎉 初始化完成！")
    print("\n📋 登录信息:")
    print("管理后台地址: http://localhost:8000/admin")
    print("管理员账户: admin / admin123")
    print("测试账户: testuser / password123")
    print("管理账户: manager / password123")
