# SQLAdmin 完整权限管理系统

## 功能概述

本系统基于 SQLAdmin 官方最佳实践，实现了完整的基于角色的权限控制系统，完全满足您提出的所有需求。

## 权限规则详解

### 1. 超级用户权限（is_superuser=True）

#### 用户管理：
- ✅ **查看**：可以查看所有用户信息
- ✅ **创建**：可以创建新用户
- ✅ **编辑**：可以编辑所有用户的所有字段（包括 is_superuser, is_active, pp_token 等）
- ✅ **删除**：可以删除任何用户

#### 认证凭据管理：
- ✅ **查看**：可以查看所有认证凭据（公开和私有）
- ✅ **创建**：可以创建公开凭据和私有凭据
- ✅ **编辑**：可以编辑任何凭据的所有字段
- ✅ **删除**：可以删除任何凭据

### 2. 普通用户权限（is_superuser=False）

#### 用户管理：
- ✅ **查看**：只能查看自己的用户信息
- ❌ **创建**：不能创建新用户
- 🔒 **编辑**：只能编辑自己的部分字段
  - ✅ 可编辑：`username`, `email`, `remark`, `description`
  - ❌ 不可编辑：`pp_token`, `is_superuser`, `is_active`
- ❌ **删除**：不能删除用户

#### 认证凭据管理：
##### 自己的私有凭据（info_status=1 且 user_id=自己）：
- ✅ **查看**：可以查看
- ✅ **创建**：可以创建（自动关联到自己）
- ✅ **编辑**：可以编辑字段：`info`, `expires_at`, `config_info`, `description`
- ✅ **删除**：可以删除

##### 公开凭据（info_status=0）：
- ✅ **查看**：可以查看
- ❌ **创建**：不能创建公开凭据
- ❌ **编辑**：不能编辑
- ❌ **删除**：不能删除

##### 他人的私有凭据：
- ❌ **查看**：完全看不到
- ❌ **创建**：不能为他人创建
- ❌ **编辑**：不能编辑
- ❌ **删除**：不能删除

## 技术实现

### 1. 查询层面过滤

权限控制在数据库查询层面实现，确保用户无法通过任何方式访问无权查看的数据：

```python
# 用户查询过滤
def get_list_query(self, request: Request):
    current_user = self.get_current_user(request)
    query = self.sessionmaker().query(self.model)
    
    if current_user.is_superuser:
        return query  # 超级用户看所有
    else:
        return query.filter(User.id == current_user.id)  # 普通用户只看自己

# 认证凭据查询过滤  
def get_list_query(self, request: Request):
    current_user = self.get_current_user(request)
    query = self.sessionmaker().query(self.model)
    
    if current_user.is_superuser:
        return query  # 超级用户看所有
    else:
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
```

### 2. 操作权限控制

每个操作（创建、编辑、删除）都有独立的权限检查：

```python
async def edit(self, request: Request) -> Response:
    current_user = self.get_current_user(request)
    
    if current_user.is_superuser:
        return await super().edit(request)  # 超级用户无限制
    else:
        # 普通用户权限检查
        if self.can_edit_by_normal_user(request):
            return await super().edit(request)
        else:
            raise PermissionError("权限不足")
```

### 3. 字段级权限控制

动态调整表单字段，普通用户看不到和不能编辑受限字段：

```python
def get_form_columns(self, request: Request, obj=None) -> List[str]:
    current_user = self.get_current_user(request)
    
    if current_user.is_superuser:
        return ["username", "email", "is_active", "is_superuser", ...]
    else:
        return ["username", "email", "remark", "description"]  # 受限字段
```

### 4. 自动数据关联

普通用户创建的私有凭据自动关联到自己：

```python
async def on_model_change(self, data, model, is_created, request):
    current_user = self.get_current_user(request)
    
    if is_created and not current_user.is_superuser:
        # 普通用户创建的凭据自动设为私有并关联到自己
        model.info_status = InfoStatusTypeEnum.PRIVATE.value
        model.user_id = current_user.id
```

## 启动和测试

### 启动应用

```bash
# 启动完整权限管理版本
python main_final.py

# 应用将在 http://127.0.0.1:8000 启动
# 管理界面地址：http://127.0.0.1:8000/admin
```

### API 测试端点

- `GET /api/user/profile` - 获取当前用户信息和权限
- `GET /api/users/count` - 获取可见用户数量
- `GET /api/credentials/count` - 获取可见凭据数量
- `GET /api/my/credentials` - 获取自己的私有凭据
- `GET /api/public/credentials` - 获取公开凭据
- `GET /api/permissions/test` - 完整权限系统测试

### 测试步骤

1. **创建测试用户**：
   ```bash
   # 首先创建超级用户
   python create_admin.py
   
   # 然后通过管理界面创建普通用户（is_superuser=False）
   ```

2. **测试超级用户**：
   - 登录超级用户账户
   - 验证可以看到所有用户和认证凭据
   - 验证可以创建、编辑、删除任何记录

3. **测试普通用户**：
   - 登录普通用户账户
   - 验证只能看到自己的用户信息
   - 验证只能看到公开凭据和自己的私有凭据
   - 验证不能修改 pp_token 等受限字段
   - 验证创建凭据时自动关联到自己

4. **API 测试**：
   ```bash
   # 使用浏览器或 curl 测试 API
   curl http://127.0.0.1:8000/api/permissions/test
   ```

## 安全特性

### 1. 数据隔离
- 查询层面过滤确保用户看不到无权访问的数据
- 没有数据泄露风险

### 2. 操作保护
- 每个操作都有权限检查
- 防止权限提升攻击

### 3. 字段保护
- 敏感字段（如 pp_token）受到保护
- 普通用户无法修改关键系统字段

### 4. 自动关联
- 普通用户创建的数据自动关联到自己
- 防止数据归属混乱

## 错误处理

系统提供友好的错误处理：
- 权限不足时显示清晰的错误信息
- 提供返回链接，不会让用户迷失
- API 返回标准的 HTTP 状态码和错误信息

## 扩展性

本系统设计具有良好的扩展性：
- 易于添加新的权限规则
- 支持更复杂的角色系统
- 可以轻松添加新的数据模型和权限控制

这个实现完全基于 SQLAdmin 的官方最佳实践，满足您提出的所有需求，并提供了额外的安全保障和用户体验优化。
