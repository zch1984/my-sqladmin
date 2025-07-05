"""
SQLAdmin 应用启动脚本
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import sqladmin
        import fastapi
        import uvicorn
        import sqlalchemy

        print("✓ 所有依赖包已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False


def check_database():
    """检查数据库连接"""
    try:
        from base import DATABASE_URL, postgres_engine_2
        from sqlalchemy import text

        with postgres_engine_2.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ 数据库连接正常")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        print("请检查数据库配置和连接")
        return False


def check_tables():
    """检查数据库表是否存在"""
    try:
        from base import postgres_engine_2
        from models.auth_model import User
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=postgres_engine_2)
        session = Session()

        user_count = session.query(User).count()
        session.close()

        print(f"✓ 数据库表存在，用户数量: {user_count}")
        return True
    except Exception as e:
        print(f"✗ 数据库表不存在或有问题: {e}")
        print("请运行: python init_db.py")
        return False


def start_server(host="127.0.0.1", port=8000, reload=True):
    """启动服务器"""
    print(f"启动SQLAdmin管理系统...")
    print(f"服务器地址: http://{host}:{port}")
    print(f"管理界面: http://{host}:{port}/admin")
    print("按 Ctrl+C 停止服务器")

    # 自动打开浏览器
    try:
        webbrowser.open(f"http://{host}:{port}/admin")
    except:
        pass

    # 启动uvicorn服务器
    import uvicorn

    uvicorn.run("main:app", host=host, port=port, reload=reload, log_level="info")


def main():
    """主函数"""
    print("SQLAdmin 管理系统启动检查")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        return

    # 检查数据库连接
    if not check_database():
        return

    # 检查数据库表
    if not check_tables():
        response = input("是否要初始化数据库? (y/n): ")
        if response.lower() == "y":
            print("正在初始化数据库...")
            try:
                from init_db import init_database

                init_database()
                print("数据库初始化完成!")
            except Exception as e:
                print(f"数据库初始化失败: {e}")
                return
        else:
            return

    print("\n" + "=" * 50)
    print("所有检查通过，启动服务器...")

    # 获取启动参数
    host = "127.0.0.1"
    port = 8000
    reload = True

    if len(sys.argv) > 1:
        if "--host" in sys.argv:
            host_index = sys.argv.index("--host") + 1
            if host_index < len(sys.argv):
                host = sys.argv[host_index]

        if "--port" in sys.argv:
            port_index = sys.argv.index("--port") + 1
            if port_index < len(sys.argv):
                port = int(sys.argv[port_index])

        if "--no-reload" in sys.argv:
            reload = False

    # 启动服务器
    start_server(host, port, reload)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)
