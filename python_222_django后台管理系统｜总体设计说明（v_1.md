# 项目总体设计说明（python222 Django后台管理系统）

> 版本：v1.0（总体）｜适用对象：开发/测试/运维/产品｜文档状态：草案可执行

---

## 1. 项目简介
**python222 Django后台管理系统**是一个 B/S 架构的综合管理平台，当前聚焦于：
- **用户管理**：用户基本信息、头像上传、状态启停、密码修改/重置、用户名查重。
- **角色管理**：角色增删改查、角色与菜单的权限分配。
- **菜单/权限管理**：树形菜单、路由/组件绑定、按钮级（F）权限。
- **登录与鉴权**：基于 JWT 的后端鉴权，中间件拦截请求并校验 Token，白名单放行登录与媒体文件。

系统预期将继续拓展 **训练时长采集/统计、请假审批、消息通知** 等模块，并支持从外部平台（如 DeliCloud）按计划任务抓取数据。

---

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

---

## 3. 运行环境与依赖（建议版本）
- **后端**：Python 3.12、Django 5.0.1、`django-cors-headers`、`rest_framework_jwt`、`mysqlclient`。
- **数据库**：MySQL 8.0+（字符集 `utf8mb4`）。
- **前端**：Node.js 18+/20+、Vue 3、Element Plus。
- **操作系统**：Windows 10/11（开发），Linux（生产）。

> 生产环境务必：
> 1) 关闭 `CORS_ORIGIN_ALLOW_ALL = True`，改成白名单；2) `SECRET_KEY` 使用环境变量；3) 使用强口令与只读最小权限账号连接 MySQL。

---

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

---

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

---

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

---

## 7. 前端页面概览
- **系统管理**（`/sys/*`）：
  - 用户管理：列表、查询、头像、状态、角色授权弹窗。
  - 角色管理：列表、查询、分配菜单（树形对话框）。
  - 菜单管理：树表、上/下级菜单编辑、权限标识（`perms`）。
- **登录页**：账号密码登录，登录后落地首页与动态菜单加载（基于后端返回）。

> 统一网络层：`src/util/request.js` 封装 `get/post`，集中处理超时与错误。

---

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

---

## 9. 典型请求流（登录 → 鉴权 → 动态菜单）
1. 前端在登录页提交用户名/密码 → `POST /user/login`。
2. 后端校验并使用 `rest_framework_jwt` 颁发 **JWT**；联表/原生 SQL 查询用户角色与角色菜单，汇总去重为 `menuList`；构造树（后端/前端）。
3. 前端保存 `token` 与 `menuList`，渲染侧边栏/路由；后续请求均在 `Authorization` 头中携带 `token`。
4. 中间件在非白名单路由拦截校验 `token`，非法/过期直接返回中文错误提示。

---

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

---

## 11. 日志与监控（建议）
- **后端**：启用 Django Logging，区分 `INFO/ERROR` 到不同文件；关键接口（登录、授权、删除）记录操作审计。
- **前端**：统一错误提示；可选接入 Sentry 采集前端异常。
- **任务/脚本**：为后续计划任务（数据抓取等）输出独立日志文件，便于排障。

---

## 12. 质量保障
- 单元/集成测试用例：覆盖用户、角色、菜单的增删改查、鉴权、异常分支（用户名重复、权限不足、无效 Token 等）。
- 代码规范：PEP8 / ESLint；提交前自动格式化与简单静态检查。

---

## 13. 后续工作与文档拆分计划
> 接下来将进入 **函数级文档**，逐个文件逐个函数描述“职责→参数→返回→副作用→异常→示例”。

- **后端**
  1) `user/views.py`：`LoginView.buildTreeMenu/post`、`SaveView.post`、`ActionView.get/delete`、`SearchView.post`、`CheckView.post`、`PwdView.post`、`PasswordView.get`、`StatusView.post`、`ImageView.post`、`AvatarView.post`、`JwtTestView.get`、`TestView.get`、`GrantRole.post`。
  2) `role/views.py`：`ListAllView.get`、`SearchView.post`、`SaveView.post`、`ActionView.get/delete`、`MenusView.get`、`GrantMenu.post`。
  3) `menu/views.py`：`TreeListView.buildTreeMenu/get`、`SaveView.post`、`ActionView.get/delete`。
  4) 模型与序列化：`SysUser/SysRole/SysMenu/SysUserRole/SysRoleMenu` + `*Serializer`。
  5) 中间件：`JwtAuthenticationMiddleware.process_request`。
- **前端**
  1) 组件与页面：`views/sys/user/*`、`views/sys/role/*`、`views/sys/menu/*`。
  2) 网络层：`util/request.js` 封装（拦截器、超时、错误处理）。
  3) 布局与导航：`layout/*`、`router/index.js`。

---

## 14. 变更记录
- **v1.0（2025-09-29）**：完成总体设计说明（架构、模块、目录、接口索引、运行与部署、后续计划）。

---

> 备注：如果你希望我按“用户模块 → 角色模块 → 菜单模块”的顺序继续输出**函数级文档**，我会基于当前代码逐一生成可交付的 API 说明与示例请求。



---

## 15. 用户模块 API（函数级）
> 覆盖 `user/views.py` 与相关 `models/serializers/middleware` 中的方法。所有接口默认返回统一结构：
>
> ```json
> { "code": 200, "msg": "ok", "data": { ... } }
> ```
> - **code**：200 成功；400 参数错误；401 未认证或 Token 失效；403 无权限；404 资源不存在；409 业务冲突（如用户名重复）；500 服务器异常。
> - **鉴权**：除 `/user/login`、静态/媒体文件外均需携带 `Authorization: Bearer <token>`。

### 15.1 `LoginView.buildTreeMenu(sysMenuList)`
- **职责**：将“扁平菜单列表（含 parent_id）”组装为树形结构，便于前端一次性渲染。
- **入参**：`sysMenuList: list[SysMenu]`，每项需至少包含 `id, parent_id, name, icon, path, component, menu_type, order_num, perms`。
- **返回**：`list[SysMenu]`（仅返回顶层节点，每个节点动态添加 `children: list`）。
- **算法**：双重循环构建父子关系；`parent_id == 0` 视为根。
- **复杂度**：O(n²)。若规模较大，建议：使用 `dict[id]->node` 建索引降至 O(n)。
- **边界**：
  - 孤儿节点（找不到父级）→ 可将其视为根或丢弃（当前实现视为根）。
  - 循环引用 → 建议在保存菜单时校验禁止。

### 15.2 `LoginView.post(request)`
- **URL/Method**：`POST /user/login?username=xxx&password=xxx`（当前代码使用 `request.GET` 读参，属于“POST + QueryString”的混用；后续建议改为 JSON Body）。
- **请求参数**：
  - `username`（必填）
  - `password`（必填；明文传输仅限开发期，生产需 HTTPS）
  - `rememberMe`（可选，布尔）
- **处理流程**：
  1) 查库 `SysUser(username, password)`（建议改为加盐哈希存储）。
  2) 生成 JWT（`rest_framework_jwt`）。
  3) 通过 `sys_user_role` → 取角色 → 通过 `sys_role_menu` → 汇总菜单，去重后构造 `menuList`（调用 `buildTreeMenu`）。
- **响应示例**：
  ```json
  {
    "code": 200,
    "msg": "ok",
    "data": {
      "token": "<jwt>",
      "user": {"id":1, "username":"python222", "avatar":"/media/userAvatar/a.png"},
      "menuList": [
        {"id":1,"name":"系统管理","icon":"system","path":"/sys","component":"","menu_type":"M","children":[
          {"id":4,"name":"角色管理","path":"/sys/role","component":"sys/role/index","menu_type":"C"}
        ]}
      ]
    }
  }
  ```
- **错误返回**：
  - 401：用户名或密码错误 / 账户停用。
  - 500：JWT 生成失败、数据库异常。
- **权限**：公开。

### 15.3 `SaveView.post(request)`（用户新增/更新）
- **URL/Method**：`POST /user/save`
- **Body(JSON)**：`{ id?, username, password?, email?, phonenumber?, status?, avatar?, remark? }`
  - `id` 缺省 → 新增；存在 → 更新。
  - 新增需要 `username`；`password` 缺省时可设置默认（如 `123456`，建议仅开发期）。
- **校验**：
  - `username` 唯一性（若冲突 → 409）。
  - `status` 只能取 `0/1`。
- **副作用**：
  - `create_time/ update_time` 自动维护（建议 `DateTimeField(auto_now_add/auto_now)`）。
- **响应**：返回写入后的用户对象（脱敏密码）。
- **权限**：管理员。

### 15.4 `ActionView.get/delete(request)`（用户删除）
- **URL**：`/user/action?id=<id or comma-separated>`
- **Method**：`GET` 或 `DELETE`（代码里常见两种并存；推荐使用 `DELETE`）。
- **行为**：按 `id` 删除单个或批量；删除前校验外键（如存在 `sys_user_role` 关联则需先解绑）。
- **响应**：删除条数。
- **错误**：404 资源不存在；409 存在约束无法删除。
- **权限**：管理员。

### 15.5 `SearchView.post(request)`（用户分页查询）
- **URL/Method**：`POST /user/search`
- **Body(JSON)**：`{ pageNum: 1, pageSize: 10, query: "关键字" }`
- **查询规则**：`name/username/email/phonenumber` 任意包含 `query`（示例代码使用 `name__icontains` 的同类写法）。
- **分页**：Django `Paginator`；返回 `total, pageNum, pageSize, rows`。
- **响应示例**：
  ```json
  {"code":200,"data":{"total":57,"pageNum":1,"pageSize":10,"rows":[{"id":1,"username":"python222"}]}}
  ```
- **权限**：登录用户。

### 15.6 `CheckView.post(request)`（用户名查重）
- **URL/Method**：`POST /user/check`
- **Body(JSON)**：`{ username: "xxx" }`
- **响应**：`{ exists: true/false }`；若 `exists: true` 同时附带占用者 `id` 便于前端提示。
- **权限**：管理员/登录用户均可（用于注册或修改前校验）。

### 15.7 `PwdView.post(request)`（用户自改密码）
- **URL/Method**：`POST /user/updateUserPwd`
- **Body(JSON)**：`{ oldPwd, newPwd }`
- **流程**：校验旧密码 → 写入新密码（建议加盐哈希；强度校验：长度≥8，含数字/字母/特殊符号 2 类以上）。
- **响应**：200；失败：400（弱口令/参数缺失）、401（旧密码不正确）。
- **权限**：登录用户。

### 15.8 `PasswordView.get(request)`（管理员重置密码）
- **URL/Method**：`GET /user/resetPassword?id=...`
- **行为**：将指定用户密码重置为默认或随机生成（建议走随机并短信/邮件告知）。
- **权限**：管理员。

### 15.9 `StatusView.post(request)`（启停用户）
- **URL/Method**：`POST /user/status`
- **Body(JSON)**：`{ id, status }`（`status ∈ {0,1}`）
- **权限**：管理员。

### 15.10 `ImageView.post(request)`（上传头像）
- **URL/Method**：`POST /user/uploadImage`
- **FormData**：`file`（图片）
- **存储**：保存到 `MEDIA_ROOT/userAvatar/`，返回 `url` 相对路径（供前端 `<el-avatar>` 直接使用）。
- **校验**：限制后缀/大小（如 ≤ 2MB）。
- **权限**：登录用户。

### 15.11 `AvatarView.post(request)`（更新头像地址字段）
- **URL/Method**：`POST /user/updateAvatar`
- **Body(JSON)**：`{ id, avatar }`
- **行为**：写库更新用户 `avatar` 字段。
- **权限**：登录用户（仅可更改自身）/管理员（可更改任意）。

### 15.12 `JwtTestView.get(request)` / `TestView.get(request)`
- **URL**：`GET /user/jwt_test`、`GET /user/test`
- **作用**：连通性与 Token 中间件校验示例；返回简单文本或当前用户信息。
- **权限**：`jwt_test` 需登录；`test` 可开放。

### 15.13 `GrantRole.post(request)`（为用户授权角色）
- **URL/Method**：`POST /user/grantRole`
- **Body(JSON)**：`{ userId: 1, roleIds: [1,2,3] }`
- **流程**：先清空 `sys_user_role` 中该用户的旧关联 → 批量插入新关联。
- **权限**：管理员。

### 15.14 中间件 `JwtAuthenticationMiddleware.process_request`
- **职责**：拦截非白名单请求，校验 `Authorization: Bearer <token>`。
- **异常分支**：
  - 缺失 Token → 401 `未认证`
  - 过期 Token → 401 `登录已过期`
  - 非法 Token → 401 `Token 非法`
- **白名单**：`/user/login`、`/media/*`（可扩展为 `settings.JWT_WHITELIST`）。

---

## 16. 角色模块 API（函数级）
> 覆盖 `role/views.py`。

### 16.1 `ListAllView.get(request)`（全部角色）
- **URL/Method**：`GET /role/listAll`
- **响应**：`[{id,name,code,remark}]`（按 `create_time` 或 `name` 排序）。
- **用途**：前端下拉选择、用户授权角色对话框。

### 16.2 `SearchView.post(request)`（分页查询角色）
- **URL/Method**：`POST /role/search`
- **Body(JSON)**：`{ pageNum, pageSize, query }`（`query` 匹配 `name/code`）。
- **响应**：`{ total, pageNum, pageSize, rows }`。

### 16.3 `SaveView.post(request)`（新增/更新角色）
- **URL/Method**：`POST /role/save`
- **Body(JSON)**：`{ id?, name, code?, remark? }`
- **校验**：`name` 唯一；`code` 建议唯一且满足 `^[a-zA-Z0-9:_-]{1,100}$`。
- **时间字段**：推荐将模型改为 `DateTimeField(auto_now_add/auto_now)`，避免手动填充导致 `null` 问题与长期运维隐患。
- **错误**：409 名称或 code 冲突。

### 16.4 `ActionView.get/delete(request)`（删除角色）
- **URL**：`/role/action?id=...`
- **行为**：删除前检查：
  - 是否仍被用户引用（`sys_user_role`）→ 若存在引用，返回 409 并给出占用数量。
  - 是否仍绑定菜单（`sys_role_menu`）→ 可选择级联删除或阻止删除（推荐阻止并提示先解绑）。

### 16.5 `MenusView.get(request)`（查询角色拥有的菜单）
- **URL/Method**：`GET /role/menus?roleId=...`
- **响应**：`menuIds: number[]` 或完整 `menuList`（建议只返回 ID 列表以减轻传输）。
- **用途**：前端“分配菜单”对话框的默认勾选。

### 16.6 `GrantMenu.post(request)`（为角色授权菜单）
- **URL/Method**：`POST /role/grant`
- **Body(JSON)**：`{ roleId, menuIds: number[] }`
- **流程**：清空 `sys_role_menu` 旧关联 → 批量插入新关联。
- **权限**：管理员。

---

## 17. 菜单模块 API（函数级）
> 覆盖 `menu/views.py`。

### 17.1 `TreeListView.get(request)`（查询菜单树）
- **URL/Method**：`GET /menu/treeList?query=xxx`
- **逻辑**：
  - 先基于 `query` 进行 `name__icontains` 过滤（若有）。
  - 按 `order_num` 升序。
  - 复用/实现 `buildTreeMenu` 组装树。
- **响应**：`menuList: TreeNode[]`；节点含 `id,name,icon,parent_id,order_num,path,component,menu_type,perms,children`。

### 17.2 `SaveView.post(request)`（新增/更新菜单）
- **URL/Method**：`POST /menu/save`
- **Body(JSON)**：`{ id?, name, icon?, parent_id, order_num, path?, component?, menu_type, perms?, remark? }`
- **校验**：
  - `name` 唯一；
  - `menu_type ∈ {"M","C","F"}`；
  - 当 `menu_type="C"` 时需提供 `path` 与 `component`；
  - 禁止将某节点的 `parent_id` 设为自身或其后代（循环引用）。
- **权限**：管理员。

### 17.3 `ActionView.get/delete(request)`（删除菜单）
- **URL**：`/menu/action?id=...`
- **策略**：
  - 若存在子菜单 → 返回 409，要求先删除/移动子节点；
  - 若被角色引用（`sys_role_menu`）→ 返回 409，提示先解绑。

---

## 18. 统一错误码与消息（建议）
| code | msg              | 说明 |
|-----:|------------------|------|
| 200  | ok               | 成功 |
| 400  | bad_request      | 参数缺失/校验失败 |
| 401  | unauthorized     | 未登录/Token 失效 |
| 403  | forbidden         | 权限不足 |
| 404  | not_found        | 资源不存在 |
| 409  | conflict         | 业务冲突（如重名/被引用） |
| 500  | server_error     | 未捕获异常 |

> **实现提示**：可在 Django 全局异常处理中将 `ValidationError/PermissionDenied/ObjectDoesNotExist` 等统一映射为以上结构，前端 `request.js` 只需识别 `code!=200` 即提示。

---

## 19. 示例请求（cURL）
```bash
# 登录（开发期，QueryString 版）
curl -X POST "http://localhost:8000/user/login?username=python222&password=123456"

# 用户分页
curl -H "Authorization: Bearer <jwt>" \
     -H "Content-Type: application/json" \
     -d '{"pageNum":1,"pageSize":10,"query":"python"}' \
     http://localhost:8000/user/search

# 为角色分配菜单
echo '{"roleId":2,"menuIds":[3,4,5]}' | \
  curl -H "Authorization: Bearer <jwt>" -H "Content-Type: application/json" \
       -d @- http://localhost:8000/role/grant
```

---

## 20. 数据字典补充（与代码字段对齐建议）
- `SysRole.create_time / update_time`：建议 `DateTimeField(auto_now_add=True/auto_now=True)`，避免手填 `DateField(null=True)` 导致“长期运维”时间回填问题。
- `SysUser.password`：建议 `CharField` 搭配 PBKDF2（Django `make_password/check_password`）。
- `SysMenu.menu_type`：`M=目录、C=菜单、F=按钮`；前端基于 `F.perms` 控按钮显隐。

---

## 21. 后续可选补充
1) 输出 **OpenAPI 3.1** 规范（YAML/JSON），便于前端/测试对接与接口 Mock。
2) 生成 **PDF** 版开发文档（含目录、页码、交叉引用）。
3) 增加 **审计日志**（who/when/what，含授权、删除等高危操作）。
4) 引入 **角色/菜单缓存**（登录与授权后写入 Redis；变更时失效），缓解高并发下的多表联查压力。

