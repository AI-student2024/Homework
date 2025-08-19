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

# ==================== 交互式CLI测试界面 ====================

def interactive_cli():
    """
    交互式命令行测试界面
    
    提供菜单驱动的测试选项，让用户可以：
    1. 选择不同的测试功能
    2. 输入测试参数
    3. 查看详细的测试结果
    4. 进行交互式权限验证
    """
    
    def print_menu():
        """打印主菜单"""
        print("\n" + "=" * 60)
        print("🎮 RBAC系统交互式测试界面")
        print("=" * 60)
        print("请选择测试选项:")
        print("  1. 🔐 用户登录测试")
        print("  2. 👤 用户信息查看")
        print("  3. 🔑 权限验证测试")
        print("  4. 🌐 API端点权限测试")
        print("  5. 📊 角色权限矩阵")
        print("  6. 🧪 自定义权限测试")
        print("  7. 📈 系统统计信息")
        print("  8. 🚀 运行完整自动化测试")
        print("  0. ❌ 退出测试")
        print("=" * 60)
    
    def get_user_input(prompt: str, default: str = "") -> str:
        """获取用户输入"""
        if default:
            user_input = input(f"{prompt} (默认: {default}): ").strip()
            return user_input if user_input else default
        else:
            return input(f"{prompt}: ").strip()
    
    def test_user_login():
        """交互式用户登录测试"""
        print("\n🔐 用户登录测试")
        print("-" * 40)
        
        username = get_user_input("请输入用户名")
        password = get_user_input("请输入密码")
        
        print(f"\n🔍 正在验证用户: {username}")
        
        try:
            if username in fake_users_db:
                user = fake_users_db[username]
                if user.password == password:
                    print("✅ 登录成功!")
                    print(f"👤 用户角色: {', '.join(user.roles)}")
                    
                    # 显示用户权限
                    all_permissions = set()
                    for role_name in user.roles:
                        if role := fake_roles_db.get(role_name):
                            all_permissions.update(role.permissions)
                    
                    print(f"🔑 用户权限: {', '.join(sorted(all_permissions))}")
                    print(f"🎫 访问令牌: {username}")
                    
                    return username  # 返回登录成功的用户名
                else:
                    print("❌ 登录失败: 密码错误")
            else:
                print("❌ 登录失败: 用户不存在")
        except Exception as e:
            print(f"💥 登录过程出错: {str(e)}")
        
        return None
    
    def view_user_info():
        """查看用户信息"""
        print("\n👤 用户信息查看")
        print("-" * 40)
        
        username = get_user_input("请输入要查看的用户名")
        
        if username in fake_users_db:
            user = fake_users_db[username]
            print(f"\n📋 用户信息:")
            print(f"   用户名: {user.username}")
            print(f"   角色: {', '.join(user.roles)}")
            print(f"   状态: {'启用' if not user.disabled else '禁用'}")
            
            # 显示详细权限
            print(f"\n🔑 详细权限:")
            for role_name in user.roles:
                if role := fake_roles_db.get(role_name):
                    print(f"   {role_name}: {', '.join(role.permissions)}")
        else:
            print("❌ 用户不存在")
    
    def test_permission():
        """交互式权限验证测试"""
        print("\n🔑 权限验证测试")
        print("-" * 40)
        
        username = get_user_input("请输入用户名")
        permission = get_user_input("请输入要验证的权限")
        
        print(f"\n🔍 验证用户 '{username}' 的 '{permission}' 权限")
        
        if username not in fake_users_db:
            print("❌ 用户不存在")
            return
        
        user = fake_users_db[username]
        print(f"👤 用户角色: {', '.join(user.roles)}")
        
        has_permission = False
        for role_name in user.roles:
            if role := fake_roles_db.get(role_name):
                print(f"🔑 检查角色 '{role_name}': {role.permissions}")
                if permission in role.permissions:
                    has_permission = True
                    print(f"✅ 角色 '{role_name}' 拥有所需权限")
                    break
                else:
                    print(f"❌ 角色 '{role_name}' 缺少所需权限")
        
        if has_permission:
            print("🎉 权限验证通过!")
        else:
            print("🚫 权限验证失败!")
    
    def test_api_endpoint():
        """API端点权限测试"""
        print("\n🌐 API端点权限测试")
        print("-" * 40)
        
        endpoints = [
            ("/admin-only", "delete", "管理员专用路由"),
            ("/editor-content", "update", "编辑者内容路由"),
            ("/public-content", "read", "公开内容路由"),
            ("/me", "read", "用户信息路由")
        ]
        
        print("可用的API端点:")
        for i, (path, perm, desc) in enumerate(endpoints, 1):
            print(f"  {i}. {path} - {desc} (需要权限: {perm})")
        
        try:
            choice = int(get_user_input("请选择要测试的端点 (1-4)", "1"))
            if 1 <= choice <= 4:
                endpoint = endpoints[choice - 1]
                username = get_user_input("请输入要测试的用户名")
                
                print(f"\n🔍 测试端点: {endpoint[0]}")
                print(f"   描述: {endpoint[2]}")
                print(f"   所需权限: {endpoint[1]}")
                
                if username in fake_users_db:
                    user = fake_users_db[username]
                    can_access = False
                    
                    for role_name in user.roles:
                        if role := fake_roles_db.get(role_name):
                            if endpoint[1] in role.permissions:
                                can_access = True
                                break
                    
                    if can_access:
                        print(f"✅ 用户 '{username}' 可以访问此端点")
                    else:
                        print(f"❌ 用户 '{username}' 无法访问此端点")
                else:
                    print("❌ 用户不存在")
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
    
    def show_role_matrix():
        """显示角色权限矩阵"""
        print("\n📊 角色权限矩阵")
        print("-" * 40)
        
        print("角色名称".ljust(15) + "权限列表")
        print("-" * 50)
        
        for role_name, role in fake_roles_db.items():
            permissions_str = ", ".join(role.permissions)
            print(f"{role_name.ljust(15)} {permissions_str}")
        
        # 显示权限统计
        all_permissions = set()
        for role in fake_roles_db.values():
            all_permissions.update(role.permissions)
        
        print(f"\n📈 权限统计:")
        print(f"   总权限数: {len(all_permissions)}")
        print(f"   权限列表: {', '.join(sorted(all_permissions))}")
    
    def custom_permission_test():
        """自定义权限测试"""
        print("\n🧪 自定义权限测试")
        print("-" * 40)
        
        print("可用的测试选项:")
        print("  1. 测试用户对特定权限的访问")
        print("  2. 比较两个用户的权限差异")
        print("  3. 检查角色权限包含关系")
        
        choice = get_user_input("请选择测试类型 (1-3)", "1")
        
        if choice == "1":
            username = get_user_input("请输入用户名")
            permission = get_user_input("请输入要测试的权限")
            
            if username in fake_users_db:
                user = fake_users_db[username]
                has_permission = any(
                    permission in fake_roles_db[role_name].permissions
                    for role_name in user.roles
                    if role_name in fake_roles_db
                )
                
                print(f"\n🔍 权限检查结果:")
                print(f"   用户: {username}")
                print(f"   权限: {permission}")
                print(f"   结果: {'✅ 拥有' if has_permission else '❌ 缺少'}")
            else:
                print("❌ 用户不存在")
        
        elif choice == "2":
            user1 = get_user_input("请输入第一个用户名")
            user2 = get_user_input("请输入第二个用户名")
            
            if user1 in fake_users_db and user2 in fake_users_db:
                user1_obj = fake_users_db[user1]
                user2_obj = fake_users_db[user2]
                
                # 获取用户权限
                def get_user_permissions(username):
                    user = fake_users_db[username]
                    permissions = set()
                    for role_name in user.roles:
                        if role := fake_roles_db.get(role_name):
                            permissions.update(role.permissions)
                    return permissions
                
                perm1 = get_user_permissions(user1)
                perm2 = get_user_permissions(user2)
                
                print(f"\n📊 权限比较结果:")
                print(f"   {user1} 的权限: {', '.join(sorted(perm1))}")
                print(f"   {user2} 的权限: {', '.join(sorted(perm2))}")
                print(f"   共同权限: {', '.join(sorted(perm1 & perm2))}")
                print(f"   独有权限: {', '.join(sorted(perm1 ^ perm2))}")
            else:
                print("❌ 用户不存在")
        
        elif choice == "3":
            role1 = get_user_input("请输入第一个角色名")
            role2 = get_user_input("请输入第二个角色名")
            
            if role1 in fake_roles_db and role2 in fake_roles_db:
                perm1 = set(fake_roles_db[role1].permissions)
                perm2 = set(fake_roles_db[role2].permissions)
                
                print(f"\n🔍 角色权限包含关系:")
                print(f"   {role1} 包含 {role2}: {'✅' if perm2.issubset(perm1) else '❌'}")
                print(f"   {role2} 包含 {role1}: {'✅' if perm1.issubset(perm2) else '❌'}")
                print(f"   权限相等: {'✅' if perm1 == perm2 else '❌'}")
            else:
                print("❌ 角色不存在")
    
    def show_system_stats():
        """显示系统统计信息"""
        print("\n📈 系统统计信息")
        print("-" * 40)
        
        total_users = len(fake_users_db)
        total_roles = len(fake_roles_db)
        total_permissions = set()
        
        for role in fake_roles_db.values():
            total_permissions.update(role.permissions)
        
        print(f"👥 用户统计:")
        print(f"   总用户数: {total_users}")
        for username, user in fake_users_db.items():
            print(f"     {username}: {', '.join(user.roles)}")
        
        print(f"\n🎭 角色统计:")
        print(f"   总角色数: {total_roles}")
        for role_name, role in fake_roles_db.items():
            print(f"     {role_name}: {', '.join(role.permissions)}")
        
        print(f"\n🔑 权限统计:")
        print(f"   总权限数: {len(total_permissions)}")
        print(f"   权限列表: {', '.join(sorted(total_permissions))}")
    
    # 主循环
    while True:
        print_menu()
        choice = get_user_input("请输入选项 (0-8)", "1")
        
        if choice == "0":
            print("\n👋 感谢使用RBAC测试系统，再见!")
            break
        elif choice == "1":
            test_user_login()
        elif choice == "2":
            view_user_info()
        elif choice == "3":
            test_permission()
        elif choice == "4":
            test_api_endpoint()
        elif choice == "5":
            show_role_matrix()
        elif choice == "6":
            custom_permission_test()
        elif choice == "7":
            show_system_stats()
        elif choice == "8":
            print("\n🚀 运行完整自动化测试...")
            test_rbac_system()
        else:
            print("❌ 无效选择，请重新输入")
        
        # 等待用户确认继续
        if choice != "0":
            input("\n按回车键继续...")

if __name__ == "__main__":
    """
    当直接运行此文件时，提供选择菜单
    """
    print("🔧 RBAC权限控制系统测试工具")
    print("正在初始化测试环境...")
    
    print("\n请选择运行模式:")
    print("  1. 🚀 运行完整自动化测试")
    print("  2. 🎮 启动交互式CLI测试界面")
    
    choice = input("请输入选择 (1-2): ").strip()
    
    if choice == "2":
        interactive_cli()
    else:
        # 执行自动化测试
        test_rbac_system()
        
        print("\n🎉 所有测试完成!")
        print("\n📚 使用说明:")
        print("1. 启动API服务器: uvicorn rbac_simple:app --reload")
        print("2. 访问 http://localhost:8000/docs 查看API文档")
        print("3. 使用 /token 端点获取访问令牌")
        print("4. 在请求头中添加: Authorization: Bearer <your_token>")
        print("5. 测试不同角色的权限控制")