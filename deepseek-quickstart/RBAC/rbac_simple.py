"""
基于RBAC（基于角色的访问控制）的FastAPI权限控制系统

RBAC是一种访问控制模型，通过角色来管理用户权限：
- 用户被分配到一个或多个角色
- 每个角色包含一组权限
- 用户通过角色间接获得权限

本系统实现了：
1. 用户认证（基于token）
2. 角色管理
3. 权限控制装饰器
4. 模拟数据库存储
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Dict, Callable, Optional
from functools import wraps

# 创建FastAPI应用实例
app = FastAPI()

# ==================== 数据模型定义 ====================

class User(BaseModel):
    """用户模型
    
    属性:
        username: 用户名，用作唯一标识
        password: 用户密码
        roles: 用户拥有的角色列表
        disabled: 用户是否被禁用，默认为False
    """
    username: str
    password: str
    roles: List[str]
    disabled: bool = False

class Role(BaseModel):
    """角色模型
    
    属性:
        name: 角色名称
        permissions: 该角色拥有的权限列表
    """
    name: str
    permissions: List[str]

# ==================== 模拟数据库 ====================

# 模拟用户数据库 - 在实际应用中应该使用真实的数据库
fake_users_db: Dict[str, User] = {
    "admin": User(username="admin", password="adminpass", roles=["admin"]),
    "editor": User(username="editor", password="editorpass", roles=["editor"]),
    "viewer": User(username="viewer", password="viewerpass", roles=["viewer"]),
}

# 模拟角色数据库 - 定义每个角色拥有的权限
fake_roles_db: Dict[str, Role] = {
    "admin": Role(name="admin", permissions=["create", "read", "update", "delete"]),  # 管理员拥有所有权限
    "editor": Role(name="editor", permissions=["read", "update"]),                    # 编辑者可以读取和更新
    "viewer": Role(name="viewer", permissions=["read"]),                             # 查看者只能读取
}

# ==================== 认证依赖 ====================

# OAuth2密码承载者认证方案，用于处理Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    获取当前认证用户的依赖函数
    
    参数:
        token: 从请求头中提取的Bearer token
        
    返回:
        当前认证的用户对象
        
    异常:
        HTTPException: 当token无效或用户被禁用时抛出
    """
    # 检查token是否存在于用户数据库中
    if token not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户对象
    user = fake_users_db[token]
    
    # 检查用户是否被禁用
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

# ==================== RBAC权限控制装饰器 ====================

def permission_required(permission: str):
    """
    RBAC权限控制装饰器
    
    这个装饰器用于保护API端点，确保只有拥有指定权限的用户才能访问
    
    参数:
        permission: 访问端点所需的权限名称
        
    使用示例:
        @app.get("/admin-only")
        @permission_required("delete")
        async def admin_only_route(current_user: User = Depends(get_current_user)):
            return {"message": "This is an admin-only route"}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从函数参数中获取当前用户
            current_user = kwargs.get("current_user")
            
            # 检查用户是否已认证
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # 检查用户是否拥有所需权限
            has_permission = False
            for role_name in current_user.roles:
                # 获取角色对象
                if role := fake_roles_db.get(role_name):
                    # 检查角色是否包含所需权限
                    if permission in role.permissions:
                        has_permission = True
                        break
            
            # 如果没有权限，抛出403禁止访问错误
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Require {permission} permission"
                )
            
            # 权限验证通过，执行原始函数
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# ==================== API路由定义 ====================

@app.post("/token")
async def login(username: str, password: str):
    """
    用户登录接口
    
    验证用户名和密码，返回访问令牌
    
    参数:
        username: 用户名
        password: 用户密码
        
    返回:
        包含访问令牌的字典
        
    异常:
        HTTPException: 当用户名或密码错误时抛出
    """
    # 验证用户名和密码
    if username not in fake_users_db or fake_users_db[username].password != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # 返回访问令牌（这里简化处理，直接使用用户名作为token）
    return {"access_token": username, "token_type": "bearer"}

@app.get("/admin-only")
@permission_required("delete")  # 需要delete权限，只有admin角色可以访问
async def admin_only_route(current_user: User = Depends(get_current_user)):
    """
    管理员专用路由
    
    只有拥有delete权限的用户（admin角色）才能访问
    """
    return {"message": "This is an admin-only route"}

@app.get("/editor-content")
@permission_required("update")  # 需要update权限，admin和editor角色可以访问
async def editor_content_route(current_user: User = Depends(get_current_user)):
    """
    编辑者内容路由
    
    拥有update权限的用户（admin和editor角色）可以访问
    """
    return {"message": "This is an editor content route"}

@app.get("/public-content")
@permission_required("read")  # 需要read权限，所有认证用户都可以访问
async def public_content_route(current_user: User = Depends(get_current_user)):
    """
    公开内容路由
    
    所有认证用户都可以访问（admin、editor、viewer角色都有read权限）
    """
    return {"message": "This is public content accessible to all authenticated users"}

@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    
    返回当前认证用户的详细信息
    """
    return current_user

# ==================== 模拟测试代码 ====================

def test_rbac_system():
    """
    模拟测试RBAC系统的各种功能
    
    这个函数演示了：
    1. 用户登录和token获取
    2. 不同角色的权限验证
    3. 权限控制装饰器的工作流程
    4. 错误处理机制
    """
    print("=" * 60)
    print("🚀 开始测试RBAC权限控制系统")
    print("=" * 60)
    
    # 测试数据准备
    test_cases = [
        {"username": "admin", "password": "adminpass", "description": "管理员用户"},
        {"username": "editor", "password": "editorpass", "description": "编辑者用户"},
        {"username": "viewer", "password": "viewerpass", "description": "查看者用户"},
        {"username": "admin", "password": "wrongpass", "description": "错误密码测试"},
        {"username": "nonexistent", "password": "anypass", "description": "不存在的用户测试"}
    ]
    
    print("\n📋 测试用例概览:")
    for i, case in enumerate(test_cases, 1):
        print(f"  {i}. {case['description']}: {case['username']}")
    
    print("\n" + "=" * 60)
    print("🔐 测试用户认证流程")
    print("=" * 60)
    
    # 测试用户认证
    for case in test_cases:
        print(f"\n🔍 测试: {case['description']}")
        print(f"   用户名: {case['username']}")
        print(f"   密码: {case['password']}")
        
        try:
            # 模拟登录过程
            if case['username'] in fake_users_db:
                user = fake_users_db[case['username']]
                if user.password == case['password']:
                    print(f"   ✅ 认证成功!")
                    print(f"   用户角色: {', '.join(user.roles)}")
                    
                    # 显示用户权限
                    all_permissions = set()
                    for role_name in user.roles:
                        if role := fake_roles_db.get(role_name):
                            all_permissions.update(role.permissions)
                    print(f"   用户权限: {', '.join(sorted(all_permissions))}")
                    
                    # 模拟token生成
                    token = case['username']
                    print(f"   访问令牌: {token}")
                    
                    # 测试权限验证
                    test_permissions = ["read", "update", "delete", "create"]
                    print(f"\n   🔒 权限验证测试:")
                    for permission in test_permissions:
                        has_permission = False
                        for role_name in user.roles:
                            if role := fake_roles_db.get(role_name):
                                if permission in role.permissions:
                                    has_permission = True
                                    break
                        
                        status_icon = "✅" if has_permission else "❌"
                        print(f"     {permission}: {status_icon}")
                    
                else:
                    print(f"   ❌ 认证失败: 密码错误")
            else:
                print(f"   ❌ 认证失败: 用户不存在")
                
        except Exception as e:
            print(f"   💥 认证过程出错: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎭 测试角色权限矩阵")
    print("=" * 60)
    
    # 显示角色权限矩阵
    print("\n📊 角色权限矩阵:")
    print("角色名称".ljust(12) + "权限列表")
    print("-" * 40)
    
    for role_name, role in fake_roles_db.items():
        permissions_str = ", ".join(role.permissions)
        print(f"{role_name.ljust(12)} {permissions_str}")
    
    print("\n" + "=" * 60)
    print("🔐 测试API端点访问权限")
    print("=" * 60)
    
    # 测试API端点访问权限
    api_endpoints = [
        {"path": "/admin-only", "required_permission": "delete", "description": "管理员专用路由"},
        {"path": "/editor-content", "required_permission": "update", "description": "编辑者内容路由"},
        {"path": "/public-content", "required_permission": "read", "description": "公开内容路由"},
        {"path": "/me", "required_permission": "read", "description": "用户信息路由"}
    ]
    
    for endpoint in api_endpoints:
        print(f"\n🌐 测试端点: {endpoint['path']}")
        print(f"   描述: {endpoint['description']}")
        print(f"   所需权限: {endpoint['required_permission']}")
        
        # 测试不同角色的访问权限
        print("   角色访问权限:")
        for role_name, role in fake_roles_db.items():
            can_access = endpoint['required_permission'] in role.permissions
            access_icon = "✅" if can_access else "❌"
            print(f"     {role_name.ljust(12)} {access_icon}")
    
    print("\n" + "=" * 60)
    print("🧪 模拟权限控制装饰器测试")
    print("=" * 60)
    
    # 模拟权限控制装饰器的工作流程
    def simulate_permission_check(user_username: str, required_permission: str):
        """模拟权限检查过程"""
        print(f"\n🔍 模拟权限检查: 用户 '{user_username}' 需要 '{required_permission}' 权限")
        
        if user_username not in fake_users_db:
            print("   ❌ 用户不存在")
            return False
        
        user = fake_users_db[user_username]
        print(f"   👤 用户角色: {', '.join(user.roles)}")
        
        has_permission = False
        for role_name in user.roles:
            if role := fake_roles_db.get(role_name):
                print(f"   🔑 检查角色 '{role_name}': 权限 {role.permissions}")
                if required_permission in role.permissions:
                    has_permission = True
                    print(f"   ✅ 角色 '{role_name}' 拥有所需权限")
                    break
                else:
                    print(f"   ❌ 角色 '{role_name}' 缺少所需权限")
        
        if has_permission:
            print("   🎉 权限验证通过!")
        else:
            print("   🚫 权限验证失败!")
        
        return has_permission
    
    # 测试不同权限组合
    test_permissions = [
        ("admin", "delete"),
        ("editor", "update"),
        ("viewer", "read"),
        ("admin", "read"),
        ("editor", "delete"),
        ("viewer", "update")
    ]
    
    for username, permission in test_permissions:
        simulate_permission_check(username, permission)
    
    print("\n" + "=" * 60)
    print("📈 测试结果统计")
    print("=" * 60)
    
    # 统计测试结果
    total_users = len(fake_users_db)
    total_roles = len(fake_roles_db)
    total_permissions = set()
    
    for role in fake_roles_db.values():
        total_permissions.update(role.permissions)
    
    print(f"\n📊 系统统计:")
    print(f"   用户总数: {total_users}")
    print(f"   角色总数: {total_roles}")
    print(f"   权限总数: {len(total_permissions)}")
    print(f"   权限列表: {', '.join(sorted(total_permissions))}")
    
    print("\n" + "=" * 60)
    print("🎯 测试完成!")
    print("=" * 60)
    print("💡 提示: 运行 'python rbac_simple.py' 来执行这些测试")
    print("🚀 或者启动FastAPI服务器: 'uvicorn rbac_simple:app --reload'")

if __name__ == "__main__":
    """
    当直接运行此文件时，执行测试代码
    """
    print("🔧 RBAC权限控制系统测试工具")
    print("正在初始化测试环境...")
    
    # 执行测试
    test_rbac_system()
    
    print("\n🎉 所有测试完成!")
    print("\n📚 使用说明:")
    print("1. 启动API服务器: uvicorn rbac_simple:app --reload")
    print("2. 访问 http://localhost:8000/docs 查看API文档")
    print("3. 使用 /token 端点获取访问令牌")
    print("4. 在请求头中添加: Authorization: Bearer <your_token>")
    print("5. 测试不同角色的权限控制")