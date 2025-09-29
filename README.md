# 项目总体设计说明（python222 Django后台管理系统）

> 版本：v1.0（总体）｜适用对象：开发/测试/运维/产品｜文档状态：草案可执行

------

## 1. 项目简介

**python222 Django后台管理系统**是一个 B/S 架构的综合管理平台，当前聚焦于：

- **用户管理**：用户基本信息、头像上传、状态启停、密码修改/重置、用户名查重。
- **角色管理**：角色增删改查、角色与菜单的权限分配。
- **菜单/权限管理**：树形菜单、路由/组件绑定、按钮级（F）权限。
- **登录与鉴权**：基于 JWT 的后端鉴权，中间件拦截请求并校验 Token，白名单放行登录与媒体文件。

系统预期将继续拓展 **训练时长采集/统计、请假审批、消息通知** 等模块，并支持从外部平台（如 DeliCloud）按计划任务抓取数据。

------

## 2. 整体架构

- **前端**：Vue 3 + Element Plus + Vue Router + Axios（`src/util/request.js` 统一封装；默认 `baseUrl = http://localhost:8000/`）。
- **后端**：Django 5（类视图）、MySQL（`django.db.backends.mysql`）、跨域 `django-cors-headers`、JWT（`rest_framework_jwt`）。
- **接口风格**：REST 风格，模块化路由 `/user/*`、`/role/*`、`/menu/*`。
- **部署拓扑（建议）**：Nginx（静态/反向代理）→ uWSGI/Gunicorn（Django）→ MySQL；前端静态资源由 Nginx 提供。

### 2.1 安全与鉴权

- **中间件**：`user.middleware.JwtAuthenticationMiddleware`
  - 白名单：`/user/login` 与媒体路径 `/media/*`。
  - 校验：读取请求头 `Authorization`，通过 `rest_framework_jwt` 的 `JWT_DECODE_HANDLER` 解码校验；过期/非法/异常分别返回中文提示。
- **权限模型**：用户 ↔ 角色（`SysUserRole`），角色 ↔ 菜单（`SysRoleMenu`），菜单含 **目录（M）/菜单（C）/按钮（F）** 三类。

------

## 3. 运行环境与依赖（建议版本）

- **后端**：Python 3.12、Django 5.0.1、`django-cors-headers`、`rest_framework_jwt`、`mysqlclient`。
- **数据库**：MySQL 8.0+（字符集 `utf8mb4`）。
- **前端**：Node.js 18+/20+、Vue 3、Element Plus。
- **操作系统**：Windows 10/11（开发），Linux（生产）。

> 生产环境务必：
>
> 1. 关闭 `CORS_ORIGIN_ALLOW_ALL = True`，改成白名单；2) `SECRET_KEY` 使用环境变量；3) 使用强口令与只读最小权限账号连接 MySQL。

------

## 4. 目录结构（关键项）

```
DjangoProject/
  manage.py
  DjangoProject/
    settings.py         # 数据库、CORS、静态/媒体路径、已安装应用、JWT 中间件
    urls.py             # 汇总路由：user/ role/ menu/ 及 media 映射
  user/                 # 用户模块
    models.py           # SysUser 模型 + Serializer
    views.py            # 登录、头像、密码、查重、授权等类视图
    urls.py             # /user/* 路由
    middleware.py       # JwtAuthenticationMiddleware
  role/                 # 角色模块
    models.py           # SysRole、SysUserRole + Serializer
    views.py            # 角色列表/分页/保存/删除/授权等
    urls.py             # /role/* 路由
  menu/                 # 菜单/权限模块
    models.py           # SysMenu、SysRoleMenu + Serializer
    views.py            # 菜单树、保存、删除
    urls.py             # /menu/* 路由
  media/
    userAvatar/         # 头像上传目录（settings.MEDIA_ROOT）
  python222_vue3_admin3/
    src/
      layout/           # 布局与导航容器
      views/sys/        # 用户/角色/菜单页面及弹窗组件
      util/request.js   # Axios 封装，统一异常处理与超时
      router/index.js   # 路由定义（登录页、首页、系统页）
```

------

## 5. 数据库设计（概要）

> 详细字段说明与约束将在“数据字典”章节给出（函数级文档阶段会对读写代码一一映射）。

### 5.1 核心实体

- **SysUser（sys_user）**
  - 字段示例：`id, username(唯一), password, avatar, email, phonenumber, login_date, status(0/1), create_time, update_time, remark`
- **SysRole（sys_role）**
  - 字段示例：`id, name, code, create_time(auto_now_add), update_time(auto_now), remark`
- **SysMenu（sys_menu）**
  - 字段示例：`id, name(唯一), icon, parent_id, order_num, path, component, menu_type(M/C/F), perms, create_time, update_time, remark`
- **SysUserRole（sys_user_role）**：`user_id ↔ role_id` 多对多桥接。
- **SysRoleMenu（sys_role_menu）**：`role_id ↔ menu_id` 多对多桥接。

### 5.2 关系说明

- 一个用户可拥有多个角色；一个角色可对应多个菜单（权限）。
- 前端通过用户所拥有角色汇总得到菜单集合，再组装成树（后端 `buildTreeMenu` 支持）。

------

## 6. 接口与模块概览

> 这里给出“入口级索引”。具体到**每个类/函数的入参、出参、异常、边界**会在下一阶段的“函数级文档”中详细展开。

### 6.1 用户模块 `/user/*`

- `POST /user/login`：登录与发放 JWT；聚合角色→菜单，返回用户信息、`menuList`、`token`。
- `POST /user/save`：新增/修改用户。
- `POST /user/search`：分页查询（`pageNum/pageSize/query`）。
- `GET  /user/action?id=...`、`DELETE /user/action?id=...`：单个/批量删除。
- `POST /user/check`：用户名查重。
- `POST /user/updateUserPwd`：用户自改密码。
- `GET  /user/resetPassword?id=...`：管理员重置密码。
- `POST /user/status`：启停用户状态。
- `POST /user/uploadImage`：上传头像（写入 `MEDIA_ROOT/userAvatar/`）。
- `POST /user/updateAvatar`：更新头像路径字段。
- `GET  /user/jwt_test`、`GET /user/test`：辅助/联调。
- `POST /user/grantRole`：为用户授权角色。

### 6.2 角色模块 `/role/*`

- `GET  /role/listAll`：获取全部角色（下拉选择等）。
- `POST /role/search`：分页查询角色。
- `POST /role/save`：新增/更新角色。
- `GET  /role/action?id=...`、`DELETE /role/action?id=...`：删除角色。
- `GET  /role/menus?roleId=...`：按角色查询已分配菜单。
- `POST /role/grant`：为角色分配菜单权限。

### 6.3 菜单模块 `/menu/*`

- `GET  /menu/treeList?query=...`：查询并构造菜单树（含关键字过滤）。
- `POST /menu/save`：新增/更新菜单。
- `GET  /menu/action?id=...`、`DELETE /menu/action?id=...`：删除菜单。

------

## 7. 前端页面概览

- **系统管理**（`/sys/*`）：
  - 用户管理：列表、查询、头像、状态、角色授权弹窗。
  - 角色管理：列表、查询、分配菜单（树形对话框）。
  - 菜单管理：树表、上/下级菜单编辑、权限标识（`perms`）。
- **登录页**：账号密码登录，登录后落地首页与动态菜单加载（基于后端返回）。

> 统一网络层：`src/util/request.js` 封装 `get/post`，集中处理超时与错误。

------

## 8. 配置要点（settings.py）

- **数据库**：

  ```python
  DATABASES = {
    'default': {
      'ENGINE': 'django.db.backends.mysql',
      'NAME': 'db_admin2', 'USER': 'root', 'PASSWORD': '1234',
      'HOST': 'localhost', 'PORT': '3306'
    }
  }
  ```

  > 生产建议：使用只读/读写分离账号；密码走环境变量；开启连接池与超时；按需启用二库（读）配置。

- **静态/媒体**：`MEDIA_URL = 'media/'`；`MEDIA_ROOT = BASE_DIR / 'media'`（头像目录 `media/userAvatar/`）。

- **跨域**：`CORS_ORIGIN_ALLOW_ALL = True`（开发期）；生产改为白名单 `CORS_ALLOWED_ORIGINS`。

- **中间件**：启用 `CorsMiddleware` + 自定义 `JwtAuthenticationMiddleware`。

------

## 9. 典型请求流（登录 → 鉴权 → 动态菜单）

1. 前端在登录页提交用户名/密码 → `POST /user/login`。
2. 后端校验并使用 `rest_framework_jwt` 颁发 **JWT**；联表/原生 SQL 查询用户角色与角色菜单，汇总去重为 `menuList`；构造树（后端/前端）。
3. 前端保存 `token` 与 `menuList`，渲染侧边栏/路由；后续请求均在 `Authorization` 头中携带 `token`。
4. 中间件在非白名单路由拦截校验 `token`，非法/过期直接返回中文错误提示。

------

## 10. 启动与部署

### 10.1 本地开发

- **后端**：

  ```bash
  # 安装依赖
  pip install -r requirements.txt  # 若无文件：手动安装 django, mysqlclient, djangorestframework-jwt, django-cors-headers
  # 初始化数据库
  python manage.py makemigrations && python manage.py migrate
  # 运行
  python manage.py runserver 0.0.0.0:8000
  ```

- **前端**：

  ```bash
  cd python222_vue3_admin3
  npm install
  npm run serve
  ```

  如需对接后端，确保 `src/util/request.js` 的 `baseUrl` 指向后端地址（开发默认 `http://localhost:8000/`）。

### 10.2 生产部署（建议）

- 前端打包后由 **Nginx** 提供静态资源；后端使用 **uWSGI/Gunicorn** 托管 Django。
- 配置 HTTPS、反向代理、访问日志、限流；分离媒体与静态目录；定期备份数据库。

------

## 11. 日志与监控（建议）

- **后端**：启用 Django Logging，区分 `INFO/ERROR` 到不同文件；关键接口（登录、授权、删除）记录操作审计。
- **前端**：统一错误提示；可选接入 Sentry 采集前端异常。
- **任务/脚本**：为后续计划任务（数据抓取等）输出独立日志文件，便于排障。

------

## 12. 质量保障

- 单元/集成测试用例：覆盖用户、角色、菜单的增删改查、鉴权、异常分支（用户名重复、权限不足、无效 Token 等）。
- 代码规范：PEP8 / ESLint；提交前自动格式化与简单静态检查。

------

## 13. 后续工作与文档拆分计划

> 接下来将进入 **函数级文档**，逐个文件逐个函数描述“职责→参数→返回→副作用→异常→示例”。

- **后端**
  1. `user/views.py`：`LoginView.buildTreeMenu/post`、`SaveView.post`、`ActionView.get/delete`、`SearchView.post`、`CheckView.post`、`PwdView.post`、`PasswordView.get`、`StatusView.post`、`ImageView.post`、`AvatarView.post`、`JwtTestView.get`、`TestView.get`、`GrantRole.post`。
  2. `role/views.py`：`ListAllView.get`、`SearchView.post`、`SaveView.post`、`ActionView.get/delete`、`MenusView.get`、`GrantMenu.post`。
  3. `menu/views.py`：`TreeListView.buildTreeMenu/get`、`SaveView.post`、`ActionView.get/delete`。
  4. 模型与序列化：`SysUser/SysRole/SysMenu/SysUserRole/SysRoleMenu` + `*Serializer`。
  5. 中间件：`JwtAuthenticationMiddleware.process_request`。
- **前端**
  1. 组件与页面：`views/sys/user/*`、`views/sys/role/*`、`views/sys/menu/*`。
  2. 网络层：`util/request.js` 封装（拦截器、超时、错误处理）。
  3. 布局与导航：`layout/*`、`router/index.js`。

------

## 14. 变更记录

- **v1.0（2025-09-29）**：完成总体设计说明（架构、模块、目录、接口索引、运行与部署、后续计划）。

------

> 备注：如果你希望我按“用户模块 → 角色模块 → 菜单模块”的顺序继续输出**函数级文档**，我会基于当前代码逐一生成可交付的 API 说明与示例请求。