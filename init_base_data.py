#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
企业管理系统基础数据初始化脚本
使用方法：
1. 确保已运行 python manage.py migrate 创建数据库表
2. 在 DjangoProject 目录下执行：python init_base_data.py
"""

import os
import sys
import django
from datetime import datetime

# 设置 Django 环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from user.models import SysUser
from role.models import SysRole, SysUserRole
from menu.models import SysMenu, SysRoleMenu


def clear_data():
    """清空现有数据（可选）"""
    print("⚠️  是否清空现有数据？(y/n): ", end="")
    choice = input().strip().lower()
    if choice == 'y':
        SysRoleMenu.objects.all().delete()
        SysUserRole.objects.all().delete()
        SysMenu.objects.all().delete()
        SysRole.objects.all().delete()
        SysUser.objects.all().delete()
        print("✓ 已清空现有数据")
    else:
        print("✓ 保留现有数据")


def create_roles():
    """创建角色数据"""
    print("\n[1/5] 创建角色数据...")

    roles = [
        {'id': 1, 'name': '超级管理员', 'code': 'admin', 'remark': '拥有系统所有权限'},
        {'id': 2, 'name': '普通管理员', 'code': 'manager', 'remark': '拥有业务管理权限'},
        {'id': 3, 'name': '普通用户', 'code': 'user', 'remark': '只有基础查看和个人操作权限'},
        {'id': 4, 'name': '正式队员', 'code': 'member', 'remark': '可查看训练时长、提交请假申请'},
    ]

    for role_data in roles:
        role, created = SysRole.objects.get_or_create(
            id=role_data['id'],
            defaults={
                'name': role_data['name'],
                'code': role_data['code'],
                'remark': role_data['remark']
            }
        )
        if created:
            print(f"  ✓ 创建角色: {role.name} ({role.code})")
        else:
            print(f"  - 角色已存在: {role.name}")


def create_menus():
    """创建菜单数据"""
    print("\n[2/5] 创建菜单数据...")

    # 一级菜单
    menus = [
        {'id': 1, 'name': '首页', 'icon': 'el-icon-s-home', 'parent_id': 0, 'order_num': 1,
         'path': '/index', 'component': 'views/index/index.vue', 'menu_type': 'C', 'perms': None, 'remark': '系统首页'},

        {'id': 2, 'name': '系统管理', 'icon': 'el-icon-setting', 'parent_id': 0, 'order_num': 2,
         'path': '/sys', 'component': None, 'menu_type': 'M', 'perms': None, 'remark': '系统管理目录'},

        {'id': 3, 'name': '业务管理', 'icon': 'el-icon-s-order', 'parent_id': 0, 'order_num': 3,
         'path': '/bsns', 'component': None, 'menu_type': 'M', 'perms': None, 'remark': '业务管理目录'},

        {'id': 4, 'name': '个人中心', 'icon': 'el-icon-user', 'parent_id': 0, 'order_num': 4,
         'path': '/userCenter', 'component': 'views/userCenter/index', 'menu_type': 'C', 'perms': None, 'remark': '个人中心'},

        # 系统管理子菜单
        {'id': 11, 'name': '用户管理', 'icon': 'el-icon-user-solid', 'parent_id': 2, 'order_num': 1,
         'path': '/sys/user', 'component': 'views/sys/user/index.vue', 'menu_type': 'C', 'perms': 'sys:user:list', 'remark': '用户管理页面'},

        {'id': 12, 'name': '角色管理', 'icon': 'el-icon-s-custom', 'parent_id': 2, 'order_num': 2,
         'path': '/sys/role', 'component': 'views/sys/role/index.vue', 'menu_type': 'C', 'perms': 'sys:role:list', 'remark': '角色管理页面'},

        {'id': 13, 'name': '菜单管理', 'icon': 'el-icon-menu', 'parent_id': 2, 'order_num': 3,
         'path': '/sys/menu', 'component': 'views/sys/menu/index.vue', 'menu_type': 'C', 'perms': 'sys:menu:list', 'remark': '菜单管理页面'},

        # 业务管理子菜单
        {'id': 21, 'name': '部门管理', 'icon': 'el-icon-office-building', 'parent_id': 3, 'order_num': 1,
         'path': '/bsns/department', 'component': 'views/bsns/Department', 'menu_type': 'C', 'perms': 'bsns:dept:list', 'remark': '部门管理页面'},

        {'id': 22, 'name': '岗位管理', 'icon': 'el-icon-suitcase', 'parent_id': 3, 'order_num': 2,
         'path': '/bsns/post', 'component': 'views/bsns/Post', 'menu_type': 'C', 'perms': 'bsns:post:list', 'remark': '岗位管理页面'},

        {'id': 23, 'name': '训练时长总览', 'icon': 'el-icon-data-line', 'parent_id': 3, 'order_num': 3,
         'path': '/bsns/trainingOverview', 'component': 'views/bsns/TrainingOverview.vue', 'menu_type': 'C', 'perms': 'bsns:training:view', 'remark': '个人训练数据总览'},

        {'id': 24, 'name': '训练记录管理', 'icon': 'el-icon-document', 'parent_id': 3, 'order_num': 4,
         'path': '/bsns/trainingAdmin', 'component': 'views/bsns/TrainingAdmin.vue', 'menu_type': 'C', 'perms': 'bsns:training:admin', 'remark': '训练记录管理（管理员）'},

        {'id': 25, 'name': '我的请假', 'icon': 'el-icon-edit', 'parent_id': 3, 'order_num': 5,
         'path': '/bsns/leaveMy', 'component': 'views/bsns/LeaveMy.vue', 'menu_type': 'C', 'perms': 'bsns:leave:my', 'remark': '我的请假申请'},

        {'id': 26, 'name': '请假管理', 'icon': 'el-icon-s-check', 'parent_id': 3, 'order_num': 6,
         'path': '/bsns/leaveAdmin', 'component': 'views/bsns/LeaveAdmin.vue', 'menu_type': 'C', 'perms': 'bsns:leave:admin', 'remark': '请假审批管理（管理员）'},

        {'id': 27, 'name': '考勤同步', 'icon': 'el-icon-refresh', 'parent_id': 3, 'order_num': 7,
         'path': '/bsns/attendanceSyncAdmin', 'component': 'views/bsns/AttendanceSyncAdmin.vue', 'menu_type': 'C', 'perms': 'bsns:attendance:sync', 'remark': '考勤数据同步（管理员）'},
    ]

    for menu_data in menus:
        menu, created = SysMenu.objects.get_or_create(
            id=menu_data['id'],
            defaults={
                'name': menu_data['name'],
                'icon': menu_data['icon'],
                'parent_id': menu_data['parent_id'],
                'order_num': menu_data['order_num'],
                'path': menu_data['path'],
                'component': menu_data['component'],
                'menu_type': menu_data['menu_type'],
                'perms': menu_data['perms'],
                'create_time': datetime.now().date(),
                'update_time': datetime.now().date(),
                'remark': menu_data['remark']
            }
        )
        if created:
            print(f"  ✓ 创建菜单: {menu.name} ({menu.path})")
        else:
            print(f"  - 菜单已存在: {menu.name}")


def create_admin_user():
    """创建管理员用户"""
    print("\n[3/5] 创建管理员用户...")

    # 使用 Django 的密码加密
    password_hash = make_password('admin123')

    user, created = SysUser.objects.get_or_create(
        username='admin',
        defaults={
            'password': password_hash,
            'email': 'admin@example.com',
            'phonenumber': '13800138000',
            'status': 0,
            'create_time': datetime.now().date(),
            'update_time': datetime.now().date(),
            'remark': '系统超级管理员',
            'violation_count': 0
        }
    )

    if created:
        print(f"  ✓ 创建管理员: {user.username}")
        print(f"    用户名: admin")
        print(f"    密码: admin123")
    else:
        print(f"  - 管理员已存在: {user.username}")


def assign_role_menus():
    """分配角色菜单权限"""
    print("\n[4/5] 分配角色菜单权限...")

    # 超级管理员 - 所有菜单
    admin_role = SysRole.objects.get(id=1)
    admin_menus = [1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 24, 25, 26, 27]

    # 普通管理员 - 业务管理权限
    manager_role = SysRole.objects.get(id=2)
    manager_menus = [1, 3, 4, 21, 22, 23, 24, 25, 26, 27]

    # 普通用户 - 基础查看权限
    user_role = SysRole.objects.get(id=3)
    user_menus = [1, 4, 23, 25]

    # 正式队员 - 训练时长总览、我的请假
    member_role = SysRole.objects.get(id=4)
    member_menus = [1, 4, 23, 25]

    role_menu_map = {
        admin_role: admin_menus,
        manager_role: manager_menus,
        user_role: user_menus,
        member_role: member_menus
    }

    for role, menu_ids in role_menu_map.items():
        for menu_id in menu_ids:
            menu = SysMenu.objects.get(id=menu_id)
            _, created = SysRoleMenu.objects.get_or_create(
                role=role,
                menu=menu
            )
            if created:
                print(f"  ✓ {role.name} -> {menu.name}")


def assign_user_roles():
    """分配用户角色"""
    print("\n[5/5] 分配用户角色...")

    admin_user = SysUser.objects.get(username='admin')
    admin_role = SysRole.objects.get(id=1)

    _, created = SysUserRole.objects.get_or_create(
        user=admin_user,
        role=admin_role
    )

    if created:
        print(f"  ✓ 用户 {admin_user.username} -> 角色 {admin_role.name}")
    else:
        print(f"  - 用户角色已存在")


def main():
    """主函数"""
    print("=" * 60)
    print("企业管理系统基础数据初始化")
    print("=" * 60)

    try:
        # 可选：清空现有数据
        # clear_data()

        # 创建基础数据
        create_roles()
        create_menus()
        create_admin_user()
        assign_role_menus()
        assign_user_roles()

        print("\n" + "=" * 60)
        print("✓✓✓ 基础数据初始化完成！")
        print("=" * 60)
        print("\n登录信息：")
        print("  用户名: admin")
        print("  密码: admin123")
        print("\n角色说明：")
        print("  1. 超级管理员（admin）- 拥有所有权限")
        print("  2. 普通管理员（manager）- 拥有业务管理权限")
        print("  3. 普通用户（user）- 只有基础查看权限")
        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
