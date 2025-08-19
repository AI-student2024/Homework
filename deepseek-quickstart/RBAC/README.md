# RBAC权限控制系统使用指南

## 📖 项目概述

这是一个基于FastAPI实现的RBAC（基于角色的访问控制）权限控制系统。RBAC是一种访问控制模型，通过角色来管理用户权限，使得权限管理更加灵活和可维护。

### 🎯 系统特点

- **用户认证**：基于OAuth2 Bearer Token的认证机制
- **角色管理**：支持多角色分配和权限继承
- **权限控制**：装饰器驱动的API端点权限保护
- **灵活配置**：易于扩展和自定义的权限系统
- **完整测试**：包含自动化测试和交互式CLI测试

## 🏗️ 系统架构

### 核心组件

```
RBAC系统
├── 数据模型 (User, Role)
├── 认证依赖 (OAuth2PasswordBearer)
├── 权限装饰器 (@permission_required)
├── API路由 (FastAPI endpoints)
├── 模拟数据库 (fake_users_db, fake_roles_db)
└── 测试工具 (自动化测试 + 交互式CLI)
```

### 权限模型

```
用户 (User)
├── 用户名 (username)
├── 密码 (password)
├── 角色列表 (roles)
└── 状态 (disabled)

角色 (Role)
├── 角色名 (name)
└── 权限列表 (permissions)

权限 (Permissions)
├── create - 创建权限
├── read - 读取权限
├── update - 更新权限
└── delete - 删除权限
```

## 🔧 安装和运行

### 环境要求

- Python 3.7+
- FastAPI
- Uvicorn

### 安装依赖

```bash
pip install fastapi uvicorn
```

### 运行方式

#### 1. 启动API服务器

```bash
uvicorn rbac_simple:app --reload
```

服务器将在 `http://localhost:8000` 启动

#### 2. 运行测试工具

```bash
python rbac_simple.py
```

选择运行模式：
- 选项1：运行完整自动化测试
- 选项2：启动交互式CLI测试界面

## 📚 API文档

### 认证端点

#### POST /token
用户登录获取访问令牌

**请求参数：**
- `username`: 用户名
- `password`: 密码

**响应示例：**
```json
{
  "access_token": "admin",
  "token_type": "bearer"
}
```

### 受保护的端点

#### GET /admin-only
管理员专用路由，需要 `delete` 权限

#### GET /editor-content
编辑者内容路由，需要 `update` 权限

#### GET /public-content
公开内容路由，需要 `read` 权限

#### GET /me
获取当前用户信息，需要 `read` 权限

## 🔐 权限控制机制

### 权限检查函数

系统使用 `check_permission(user, required_permission)` 函数来验证用户权限：

```python
def check_permission(user: User, required_permission: str) -> bool:
    """检查用户是否拥有指定权限"""
    for role_name in user.roles:
        if role := fake_roles_db.get(role_name):
            if required_permission in role.permissions:
                return True
    return False
```

### 权限验证流程

1. **用户认证**：验证Bearer Token
2. **角色获取**：从用户信息中提取角色列表
3. **权限检查**：调用 `check_permission()` 函数验证权限
4. **访问控制**：根据权限验证结果决定是否允许访问

### API端点权限配置

```python
@app.get("/admin-only")
async def admin_only_route(current_user: User = Depends(get_current_user)):
    # 检查用户是否拥有delete权限
    if not check_permission(current_user, "delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Require delete permission"
        )
    return {"message": "This is an admin-only route"}
```

### 默认用户和角色

#### 用户列表
- `admin` / `adminpass` - 管理员用户
- `editor` / `editorpass` - 编辑者用户  
- `viewer` / `viewerpass` - 查看者用户

#### 角色权限
- **admin**: `create`, `read`, `update`, `delete`
- **editor**: `read`, `update`
- **viewer**: `read`

## 🧪 测试指南

### 自动化测试

运行完整的自动化测试套件：

```bash
python rbac_simple.py
# 选择选项 1
```

测试内容包括：
- 用户认证流程
- 角色权限矩阵
- API端点访问权限
- 权限检查函数
- 系统统计信息

### curl命令行测试

curl是测试REST API最常用的命令行工具，以下是详细的测试方法：

#### 环境准备

确保FastAPI服务器正在运行：
```bash
uvicorn rbac_simple:app --reload
```

#### 基本测试流程

1. **获取访问令牌**
2. **使用令牌访问受保护的端点**
3. **验证权限控制是否正常工作**

#### 测试技巧

- 使用 `-v` 参数查看详细的HTTP请求和响应
- 使用 `-w "%{http_code}"` 只显示HTTP状态码
- 使用 `-s` 参数静默模式，不显示进度条
- 使用 `-H` 参数设置请求头
- 使用 `-d` 参数发送POST数据

### 交互式CLI测试

启动交互式测试界面：

```bash
python rbac_simple.py
# 选择选项 2
```

#### 测试选项

1. **🔐 用户登录测试**
   - 手动输入用户名和密码
   - 查看认证结果和用户权限

2. **👤 用户信息查看**
   - 查看指定用户的详细信息
   - 显示用户角色和权限

3. **🔑 权限验证测试**
   - 测试特定用户是否拥有特定权限
   - 详细的权限检查过程

4. **🌐 API端点权限测试**
   - 测试用户对各个API端点的访问权限
   - 模拟真实的API访问场景

5. **📊 角色权限矩阵**
   - 显示所有角色的权限分布
   - 权限统计信息

6. **🧪 自定义权限测试**
   - 权限包含关系检查
   - 用户权限比较
   - 自定义权限验证

7. **📈 系统统计信息**
   - 用户、角色、权限总数
   - 详细的系统概览

8. **🚀 运行完整自动化测试**
   - 执行所有自动化测试用例

## 💡 使用示例

### 1. 获取访问令牌

```bash
# 管理员用户登录
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=adminpass"

# 编辑者用户登录
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=editor&password=editorpass"

# 查看者用户登录
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=viewer&password=viewerpass"

# 错误密码测试
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=wrongpass"
```

### 2. 访问受保护的端点

#### 管理员专用路由 (/admin-only)
```bash
# 管理员访问（成功）
curl -X GET "http://localhost:8000/admin-only" \
     -H "Authorization: Bearer admin"

# 编辑者访问（失败 - 需要delete权限）
curl -X GET "http://localhost:8000/admin-only" \
     -H "Authorization: Bearer editor"

# 查看者访问（失败 - 需要delete权限）
curl -X GET "http://localhost:8000/admin-only" \
     -H "Authorization: Bearer viewer"

# 无认证访问（失败）
curl -X GET "http://localhost:8000/admin-only"
```

#### 编辑者内容路由 (/editor-content)
```bash
# 管理员访问（成功）
curl -X GET "http://localhost:8000/editor-content" \
     -H "Authorization: Bearer admin"

# 编辑者访问（成功）
curl -X GET "http://localhost:8000/editor-content" \
     -H "Authorization: Bearer editor"

# 查看者访问（失败 - 需要update权限）
curl -X GET "http://localhost:8000/editor-content" \
     -H "Authorization: Bearer viewer"
```

#### 公开内容路由 (/public-content)
```bash
# 管理员访问（成功）
curl -X GET "http://localhost:8000/public-content" \
     -H "Authorization: Bearer admin"

# 编辑者访问（成功）
curl -X GET "http://localhost:8000/public-content" \
     -H "Authorization: Bearer editor"

# 查看者访问（成功）
curl -X GET "http://localhost:8000/public-content" \
     -H "Authorization: Bearer viewer"
```

#### 用户信息路由 (/me)
```bash
# 获取当前用户信息
curl -X GET "http://localhost:8000/me" \
     -H "Authorization: Bearer admin"

curl -X GET "http://localhost:8000/me" \
     -H "Authorization: Bearer editor"

curl -X GET "http://localhost:8000/me" \
     -H "Authorization: Bearer viewer"
```

### 3. 完整的权限测试流程

```bash
# 步骤1: 获取管理员token
TOKEN=$(curl -s -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=adminpass" | \
     python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "获取到的token: $TOKEN"

# 步骤2: 测试所有端点
echo "测试管理员权限..."
curl -X GET "http://localhost:8000/admin-only" \
     -H "Authorization: Bearer $TOKEN"
echo ""

curl -X GET "http://localhost:8000/editor-content" \
     -H "Authorization: Bearer $TOKEN"
echo ""

curl -X GET "http://localhost:8000/public-content" \
     -H "Authorization: Bearer $TOKEN"
echo ""

curl -X GET "http://localhost:8000/me" \
     -H "Authorization: Bearer $TOKEN"
echo ""
```

### 4. 错误处理测试

```bash
# 测试无效token
curl -X GET "http://localhost:8000/admin-only" \
     -H "Authorization: Bearer invalid_token"

# 测试过期token（模拟）
curl -X GET "http://localhost:8000/admin-only" \
     -H "Authorization: Bearer expired_token"

# 测试无认证访问
curl -X GET "http://localhost:8000/admin-only"

# 测试权限不足
curl -X GET "http://localhost:8000/admin-only" \
     -H "Authorization: Bearer viewer"
```

### 5. 批量权限测试脚本

创建一个测试脚本 `test_permissions.sh`：

```bash
#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试配置
BASE_URL="http://localhost:8000"
USERS=("admin" "editor" "viewer")
PASSWORDS=("adminpass" "editorpass" "viewerpass")
ENDPOINTS=("/admin-only" "/editor-content" "/public-content" "/me")

echo "🚀 开始RBAC权限系统测试..."
echo "=================================="

for i in "${!USERS[@]}"; do
    USERNAME="${USERS[$i]}"
    PASSWORD="${PASSWORDS[$i]}"
    
    echo -e "\n${YELLOW}测试用户: $USERNAME${NC}"
    echo "----------------------------------"
    
    # 获取token
    echo "正在登录..."
    TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$USERNAME&password=$PASSWORD")
    
    if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
        TOKEN=$(echo "$TOKEN_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
        echo -e "${GREEN}✅ 登录成功，Token: $TOKEN${NC}"
        
        # 测试各个端点
        for endpoint in "${ENDPOINTS[@]}"; do
            echo -n "测试端点 $endpoint: "
            RESPONSE=$(curl -s -w "%{http_code}" -X GET "$BASE_URL$endpoint" \
                -H "Authorization: Bearer $TOKEN")
            
            HTTP_CODE="${RESPONSE: -3}"
            BODY="${RESPONSE%???}"
            
            if [ "$HTTP_CODE" = "200" ]; then
                echo -e "${GREEN}✅ 成功 (HTTP $HTTP_CODE)${NC}"
            elif [ "$HTTP_CODE" = "403" ]; then
                echo -e "${YELLOW}⚠️  权限不足 (HTTP $HTTP_CODE)${NC}"
            else
                echo -e "${RED}❌ 失败 (HTTP $HTTP_CODE)${NC}"
            fi
        done
    else
        echo -e "${RED}❌ 登录失败${NC}"
    fi
done

echo -e "\n🎯 测试完成！"
```

## 🔧 扩展和自定义

### 添加新用户

在 `fake_users_db` 中添加新用户：

```python
fake_users_db["newuser"] = User(
    username="newuser", 
    password="newpass", 
    roles=["editor"]
)
```

### 添加新角色

在 `fake_roles_db` 中添加新角色：

```python
fake_roles_db["moderator"] = Role(
    name="moderator", 
    permissions=["read", "update", "moderate"]
)
```

### 添加新权限

在角色定义中添加新权限：

```python
fake_roles_db["admin"].permissions.append("moderate")
```

### 自定义权限检查函数

创建更复杂的权限检查逻辑：

```python
def check_role_permission(user: User, required_role: str, required_permission: str) -> bool:
    """检查用户是否拥有指定角色的指定权限"""
    if required_role not in user.roles:
        return False
    return check_permission(user, required_permission)

def check_multiple_permissions(user: User, required_permissions: List[str]) -> bool:
    """检查用户是否拥有所有指定权限"""
    for permission in required_permissions:
        if not check_permission(user, permission):
            return False
    return True

def check_any_permission(user: User, required_permissions: List[str]) -> bool:
    """检查用户是否拥有任意一个指定权限"""
    for permission in required_permissions:
        if check_permission(user, permission):
            return True
    return False
```

## 🚨 注意事项

### 安全考虑

1. **生产环境**：当前使用模拟数据库，生产环境应使用真实的数据库
2. **密码安全**：实际应用中应使用加密存储密码
3. **Token管理**：实现Token过期和刷新机制
4. **权限审计**：记录权限访问日志

### 性能优化

1. **权限缓存**：缓存用户权限信息
2. **数据库索引**：为权限查询添加适当的索引
3. **批量权限检查**：优化多权限验证的性能

## 📖 相关资源

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [OAuth2规范](https://oauth.net/2/)
- [RBAC模型介绍](https://en.wikipedia.org/wiki/Role-based_access_control)
- [Python装饰器教程](https://realpython.com/primer-on-python-decorators/)

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

### 开发环境设置

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 📋 快速测试参考表

### 用户权限矩阵

| 用户角色 | create | read | update | delete | 可访问端点 |
|---------|--------|------|--------|--------|------------|
| admin   | ✅     | ✅   | ✅     | ✅     | 所有端点   |
| editor  | ❌     | ✅   | ✅     | ❌     | /editor-content, /public-content, /me |
| viewer  | ❌     | ✅   | ❌     | ❌     | /public-content, /me |

### 常见测试场景

| 测试场景 | 预期结果 | curl命令示例 |
|---------|----------|-------------|
| 管理员访问所有端点 | 全部成功 | `curl -H "Authorization: Bearer admin" http://localhost:8000/admin-only` |
| 编辑者访问管理员端点 | 403权限不足 | `curl -H "Authorization: Bearer editor" http://localhost:8000/admin-only` |
| 查看者访问编辑者端点 | 403权限不足 | `curl -H "Authorization: Bearer viewer" http://localhost:8000/editor-content` |
| 无效token访问 | 401未认证 | `curl -H "Authorization: Bearer invalid" http://localhost:8000/admin-only` |
| 无认证访问 | 422参数错误 | `curl http://localhost:8000/admin-only` |

### 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 422 Unprocessable Entity | 缺少Authorization头 | 添加 `-H "Authorization: Bearer <token>"` |
| 401 Unauthorized | Token无效或过期 | 重新调用 `/token` 端点获取新token |
| 403 Forbidden | 权限不足 | 检查用户角色和所需权限 |
| 连接被拒绝 | 服务器未启动 | 运行 `uvicorn rbac_simple:app --reload` |

---

**🎉 感谢使用RBAC权限控制系统！**

如有问题或建议，请通过Issue或Pull Request联系我们。
