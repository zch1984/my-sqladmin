# SQLAdmin 用户认证管理系统 - 使用示例

基于SQLAdmin和FastAPI的现代化用户认证管理系统已经配置完成，支持以下功能：

## 主要功能

### 1. 用户管理
- **基本信息**：用户名、邮箱、激活状态、超级管理员权限
- **密码管理**：支持密码修改，密码自动加密存储
- **PP令牌**：自动生成唯一的PP平台令牌
- **JSON字段**：description字段支持复杂JSON数据结构
- **备注信息**：支持文本备注

### 2. 认证凭据管理
- **认证信息**：存储认证相关信息
- **状态控制**：公开/私有状态管理
- **用户关联**：私有凭据关联到特定用户
- **过期时间**：支持设置凭据过期时间
- **JSON配置**：config_info和description字段支持JSON格式

### 3. JSON字段使用示例

#### 用户description字段示例：
```json
{
  "role": "系统管理员",
  "department": "技术部",
  "permissions": ["read", "write", "delete", "admin"],
  "contact": {
    "phone": "13800138000",
    "wechat": "admin_user"
  },
  "preferences": {
    "theme": "dark",
    "language": "zh-CN"
  }
}
```

#### 认证凭据config_info字段示例：
```json
{
  "api_url": "https://api.example.com/v1",
  "rate_limit": 1000,
  "timeout": 30,
  "retry_count": 3,
  "headers": {
    "User-Agent": "MyApp/1.0",
    "Accept": "application/json"
  },
  "encryption": {
    "algorithm": "AES-256",
    "key_rotation": true
  }
}
```

#### 认证凭据description字段示例：
```json
{
  "purpose": "生产环境API访问",
  "created_by": "张三",
  "approval_status": "approved",
  "security_level": "high",
  "usage_notes": "仅限生产环境使用，需要定期更新",
  "compliance": {
    "gdpr": true,
    "pci_dss": false
  }
}
```

## 密码管理

### 管理员操作：
1. **创建用户**：在表单中输入密码，系统自动加密存储
2. **修改密码**：
   - 在编辑用户页面，密码字段留空表示不修改
   - 输入新密码则更新用户密码
   - 密码自动使用bcrypt加密

### 密码安全：
- 使用bcrypt算法加密
- 密码字段在界面中不显示实际值
- 支持密码强度验证（最少6位）

## 数据状态管理

### 认证凭据状态：
- **公开 (0)**：所有用户可见，不关联特定用户
- **私有 (1)**：仅关联用户可见和管理

### 自动关联规则：
- 设置为公开时，自动清除用户关联
- 设置为私有时，需要指定关联用户

## 管理界面功能

### 列表页面：
- 支持搜索：用户名、邮箱、PP令牌等
- 支持排序：按创建时间、更新时间等排序
- JSON字段智能显示：自动格式化显示前50字符

### 编辑页面：
- JSON字段自动格式化
- 实时JSON验证
- 密码字段安全处理

### 详情页面：
- 完整信息展示
- JSON字段格式化显示
- 时间格式化显示

## 启动和使用

### 1. 启动服务
```bash
python main.py
```

### 2. 访问管理界面
```
http://localhost:8000/admin
```

### 3. API接口
```
健康检查: GET /health
用户统计: GET /api/users/count
凭据统计: GET /api/credentials/count
```

## 数据库初始化

### 初始化示例数据：
```bash
python init_db.py
```

### 重置数据库：
```bash
python init_db.py reset
```

### 默认管理员账户：
- 用户名：admin
- 密码：admin123456
- 邮箱：admin@example.com

## 扩展功能

系统设计支持以下扩展：

1. **权限控制**：可以添加基于角色的访问控制
2. **审计日志**：可以记录用户操作历史
3. **批量操作**：支持批量用户管理
4. **数据导出**：支持CSV/Excel格式导出
5. **API认证**：可以添加API密钥认证
6. **多租户**：支持多租户架构扩展

## 注意事项

1. **JSON字段**：输入必须是有效的JSON格式，系统会自动验证
2. **密码安全**：建议定期更新密码，使用强密码策略
3. **数据备份**：定期备份数据库，特别是生产环境
4. **权限管理**：合理分配用户权限，避免权限滥用
5. **监控日志**：关注系统日志，及时发现异常操作
