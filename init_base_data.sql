-- ============================================
-- 企业管理系统基础数据初始化脚本
-- ============================================
-- 说明：
-- 1. 此脚本会插入基础的角色、菜单、管理员用户数据
-- 2. 管理员账号：admin / admin123
-- 3. 执行前请确保数据库表已创建（运行 python manage.py migrate）
-- ============================================

-- ============================================
-- 1. 清空现有数据（可选，谨慎使用）
-- ============================================
-- DELETE FROM sys_role_menu;
-- DELETE FROM sys_user_role;
-- DELETE FROM sys_menu;
-- DELETE FROM sys_role;
-- DELETE FROM sys_user;

-- ============================================
-- 2. 插入角色数据
-- ============================================
INSERT INTO sys_role (id, name, code, create_time, update_time, remark) VALUES
(1, '超级管理员', 'admin', NOW(), NOW(), '拥有系统所有权限'),
(2, '普通管理员', 'manager', NOW(), NOW(), '拥有业务管理权限'),
(3, '普通用户', 'user', NOW(), NOW(), '只有基础查看和个人操作权限'),
(4, '正式队员', 'member', NOW(), NOW(), '可查看训练时长、提交请假申请');

-- ============================================
-- 3. 插入菜单数据
-- ============================================
-- 一级菜单（目录）
INSERT INTO sys_menu (id, name, icon, parent_id, order_num, path, component, menu_type, perms, create_time, update_time, remark) VALUES
(1, '首页', 'el-icon-s-home', NULL, 1, '/index', 'views/index/index.vue', 'C', NULL, NOW(), NOW(), '系统首页'),
(2, '系统管理', 'el-icon-setting', NULL, 2, '/sys', NULL, 'M', NULL, NOW(), NOW(), '系统管理目录'),
(3, '业务管理', 'el-icon-s-order', NULL, 3, '/bsns', NULL, 'M', NULL, NOW(), NOW(), '业务管理目录'),
(4, '个人中心', 'el-icon-user', NULL, 4, '/userCenter', 'views/userCenter/index', 'C', NULL, NOW(), NOW(), '个人中心');

-- 系统管理子菜单
INSERT INTO sys_menu (id, name, icon, parent_id, order_num, path, component, menu_type, perms, create_time, update_time, remark) VALUES
(11, '用户管理', 'el-icon-user-solid', 2, 1, '/sys/user', 'views/sys/user/index.vue', 'C', 'sys:user:list', NOW(), NOW(), '用户管理页面'),
(12, '角色管理', 'el-icon-s-custom', 2, 2, '/sys/role', 'views/sys/role/index.vue', 'C', 'sys:role:list', NOW(), NOW(), '角色管理页面'),
(13, '菜单管理', 'el-icon-menu', 2, 3, '/sys/menu', 'views/sys/menu/index.vue', 'C', 'sys:menu:list', NOW(), NOW(), '菜单管理页面');

-- 业务管理子菜单
INSERT INTO sys_menu (id, name, icon, parent_id, order_num, path, component, menu_type, perms, create_time, update_time, remark) VALUES
(21, '部门管理', 'el-icon-office-building', 3, 1, '/bsns/department', 'views/bsns/Department', 'C', 'bsns:dept:list', NOW(), NOW(), '部门管理页面'),
(22, '岗位管理', 'el-icon-suitcase', 3, 2, '/bsns/post', 'views/bsns/Post', 'C', 'bsns:post:list', NOW(), NOW(), '岗位管理页面'),
(23, '训练时长总览', 'el-icon-data-line', 3, 3, '/bsns/trainingOverview', 'views/bsns/TrainingOverview.vue', 'C', 'bsns:training:view', NOW(), NOW(), '个人训练数据总览'),
(24, '训练记录管理', 'el-icon-document', 3, 4, '/bsns/trainingAdmin', 'views/bsns/TrainingAdmin.vue', 'C', 'bsns:training:admin', NOW(), NOW(), '训练记录管理（管理员）'),
(25, '我的请假', 'el-icon-edit', 3, 5, '/bsns/leaveMy', 'views/bsns/LeaveMy.vue', 'C', 'bsns:leave:my', NOW(), NOW(), '我的请假申请'),
(26, '请假管理', 'el-icon-s-check', 3, 6, '/bsns/leaveAdmin', 'views/bsns/LeaveAdmin.vue', 'C', 'bsns:leave:admin', NOW(), NOW(), '请假审批管理（管理员）'),
(27, '考勤同步', 'el-icon-refresh', 3, 7, '/bsns/attendanceSyncAdmin', 'views/bsns/AttendanceSyncAdmin.vue', 'C', 'bsns:attendance:sync', NOW(), NOW(), '考勤数据同步（管理员）');

-- ============================================
-- 4. 插入管理员用户
-- ============================================
-- 注意：密码需要加密，这里使用明文 'admin123' 的示例
-- 实际使用时需要通过 Django 的密码加密机制生成
INSERT INTO sys_user (id, username, password, avatar, email, phonenumber, student_no, login_date, status, create_time, update_time, remark, violation_count) VALUES
(1, 'admin', 'pbkdf2_sha256$600000$placeholder$hash', NULL, 'admin@example.com', '13800138000', NULL, NULL, 0, NOW(), NOW(), '系统超级管理员', 0);

-- ============================================
-- 5. 分配角色权限（角色-菜单关联）
-- ============================================
-- 超级管理员（admin）- 拥有所有菜单权限
INSERT INTO sys_role_menu (role_id, menu_id) VALUES
(1, 1), (1, 2), (1, 3), (1, 4),  -- 一级菜单
(1, 11), (1, 12), (1, 13),        -- 系统管理
(1, 21), (1, 22), (1, 23), (1, 24), (1, 25), (1, 26), (1, 27);  -- 业务管理

-- 普通管理员（manager）- 拥有业务管理权限
INSERT INTO sys_role_menu (role_id, menu_id) VALUES
(2, 1), (2, 3), (2, 4),           -- 首页、业务管理、个人中心
(2, 21), (2, 22), (2, 23), (2, 24), (2, 25), (2, 26), (2, 27);  -- 所有业务管理菜单

-- 普通用户（user）- 只有基础查看权限
INSERT INTO sys_role_menu (role_id, menu_id) VALUES
(3, 1), (3, 4),                   -- 首页、个人中心
(3, 23), (3, 25);                 -- 训练时长总览、我的请假

-- 正式队员（member）- 训练时长总览、我的请假
INSERT INTO sys_role_menu (role_id, menu_id) VALUES
(4, 1), (4, 4),                   -- 首页、个人中心
(4, 23), (4, 25);                 -- 训练时长总览、我的请假

-- ============================================
-- 6. 分配用户角色（用户-角色关联）
-- ============================================
-- 将 admin 用户分配为超级管理员
INSERT INTO sys_user_role (user_id, role_id) VALUES
(1, 1);

-- ============================================
-- 完成
-- ============================================
