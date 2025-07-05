# SQLAdmin 用户认证管理系统

基于SQLAdmin和FastAPI的现代化用户认证管理系统，提供美观的Web界面来管理用户和认证凭据。

## 功能特性

### 🔐 用户管理
- 用户CRUD操作（创建、读取、更新、删除）
- 密码自动加密（bcrypt）
- 用户状态管理（激活/停用）
- 超级管理员权限控制
- PP令牌自动生成
- JSON格式的补充信息存储

### 🔑 认证凭据管理
- 认证信息管理
- 公开/私有状态控制
- 用户关联管理
- 过期时间设置
- JSON配置信息
- 批量操作支持

### 🎨 现代化界面
- 响应式设计，支持移动设备
- 美观的Bootstrap主题
- 实时表单验证
- JSON格式化工具
- 搜索和过滤功能
- 数据导出功能

### 📊 数据管理
- 高级搜索和过滤
- 分页显示
- 批量操作
- 数据导出（CSV/Excel）
- 统计信息展示

## 快速开始

### 1. 环境要求
- Python 3.8+
- PostgreSQL 数据库
- pip 包管理器

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置数据库
创建 `.env` 文件并配置数据库连接：
```env
DATABASE_URL=postgresql://用户名:密码@主机:端口/数据库名
```

### 4. 初始化数据库
```bash
python init_db.py
```

### 5. 启动应用
```bash
python run.py
```

或者直接运行：
```bash
python main.py
```

### 6. 访问管理界面
打开浏览器访问：http://localhost:8000/admin

## 默认账户

初始化后会创建以下测试账户：

**管理员账户：**
- 用户名：`admin`
- 密码：`admin123456`
- 邮箱：`admin@example.com`
- 权限：超级管理员

**普通用户：**
- 用户名：`user1`
- 密码：`user123456`
- 邮箱：`user1@example.com`

## 项目结构

```
sqladmin/
├── main.py                 # 主应用入口
├── run.py                  # 启动脚本
├── init_db.py             # 数据库初始化
├── base.py                # 数据库基础配置
├── requirements.txt       # 依赖包列表
├── README.md             # 项目说明
├── models/               # 数据模型
│   └── auth_model.py    # 用户和认证模型
├── admin/               # 管理界面配置
│   └── auth_admin.py    # SQLAdmin配置
├── static/              # 静态文件
│   ├── custom.css       # 自定义样式
│   └── custom.js        # 自定义脚本
└── dao/                 # 数据访问层（扩展用）
    └── auth_dao.py
```

## 数据模型

### User（用户表）
- `id`: 用户ID（主键）
- `username`: 用户名（唯一）
- `email`: 邮箱（唯一）
- `pp_token`: PP平台令牌（自动生成）
- `hashed_password`: 加密密码
- `is_active`: 是否激活
- `is_superuser`: 是否超级管理员
- `remark`: 备注信息
- `description`: 补充信息（JSON格式）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### AuthCredentials（认证凭据表）
- `id`: 凭据ID（主键）
- `info`: 认证信息
- `info_status`: 信息状态（0-公开，1-私有）
- `user_id`: 关联用户ID（外键）
- `expires_at`: 过期时间
- `config_info`: 配置信息（JSON格式）
- `description`: 补充信息（JSON格式）
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 配置说明

### 环境变量
在`.env`文件中配置：
```env
# 数据库连接
DATABASE_URL=postgresql://postgres:password@localhost:5432/dbname

# 可选配置
APP_HOST=127.0.0.1
APP_PORT=8000
APP_DEBUG=True
```

### 数据库配置
系统支持多种数据库：
- PostgreSQL（推荐）
- MySQL
- SQLite

## 使用指南

### 用户管理
1. 在管理界面点击"用户管理"
2. 可以创建、编辑、删除用户
3. 支持搜索和过滤用户
4. JSON字段支持复杂数据结构

### 认证凭据管理
1. 点击"认证凭据管理"
2. 创建新的认证信息
3. 设置公开/私有状态
4. 关联到特定用户（私有模式）
5. 设置过期时间

### JSON字段使用
系统支持JSON格式的复杂数据：
```json
{
  "role": "管理员",
  "permissions": ["read", "write", "delete"],
  "metadata": {
    "created_by": "system",
    "department": "技术部"
  }
}
```

## 扩展功能

### 自定义字段验证
在 `admin/auth_admin.py` 中可以添加自定义验证：
```python
def on_model_change(self, data, model, is_created):
    # 自定义验证逻辑
    pass
```

### 自定义权限控制
可以在Admin类中添加权限检查：
```python
def is_accessible(self, request):
    # 权限检查逻辑
    return True
```

## API接口

系统提供RESTful API接口：
- `GET /api/users/count` - 获取用户数量
- `GET /api/credentials/count` - 获取凭据数量
- `GET /health` - 健康检查

## 开发指南

### 添加新模型
1. 在 `models/` 目录下创建新模型
2. 在 `admin/` 目录下创建对应的Admin配置
3. 在 `main.py` 中注册新的Admin视图

### 自定义样式
编辑 `static/custom.css` 来自定义界面样式。

### 自定义脚本
编辑 `static/custom.js` 来添加前端交互功能。

## 故障排除

### 常见问题
1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接字符串是否正确
   - 确认数据库用户权限

2. **依赖包安装失败**
   - 更新pip：`pip install --upgrade pip`
   - 使用国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`

3. **表不存在错误**
   - 运行 `python init_db.py` 初始化数据库

### 重置数据库
如需重置数据库：
```bash
python init_db.py reset
python init_db.py
```

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

MIT License

## 联系方式

如有问题，请提交GitHub Issue。