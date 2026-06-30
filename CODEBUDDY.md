# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## 项目概述

CloudWeave（织云）是基于 django-vue3-admin 的综合运维管理系统，采用**前后端分离 + MCP 智能层**三层架构。面向集团公司/中小型团队，覆盖两大资产管理域——**服务器资产**（服务器/域名/IP/端口/项目）与**办公资产**（电脑/手机/SIM卡/平板）。当前处于从 django-vue3-admin 基座向 CloudWeave 运维平台演进阶段，PRD 见 `docs/运维管理系统_PRD_v2.md`。

- **后端**: Python 3.12+ / Django 4.2（目标 5.x）/ DRF 3.15 / SimpleJWT / Channels (WebSocket)
- **前端**: Vue 3.4（目标 3.5+）/ TypeScript / Vite 5.4（目标 6.x）/ Pinia / Element Plus / FastCrud / Tailwind CSS
- **MCP 智能层**: cloudweave-mcp — 将全部业务能力暴露为标准化 AI Tool，支持自然语言运维交互
- **基础设施**: PostgreSQL 16 / Redis / Celery / Docker Compose

---

## 常用命令

### Docker Compose 部署（推荐）

```bash
# 一键初始化并启动所有服务（PostgreSQL、Redis、Django、Nginx、Celery）
bash init.sh

# 手动启动
docker-compose up -d

# 首次启动后初始化数据（仅一次）
docker exec -ti dvadmin3-django bash
python manage.py makemigrations
python manage.py migrate
python manage.py init         # 初始化系统数据（菜单、角色、用户等）
python manage.py init_area    # 初始化省市县数据
exit
```

前端访问 `http://localhost:8080`，后端 API 访问 `http://localhost:8000/api/`。默认账户 `superadmin` / `admin123456`。

### 前端开发

```bash
cd web
yarn install                    # 安装依赖
yarn run dev                    # 启动开发服务器 (默认 8080 端口)
yarn run build                  # 生产构建
yarn run lint-fix               # ESLint 代码修复
```

开发时 Vite 代理后端请求到 `http://127.0.0.1:8000`（在 `.env.development` 中通过 `VITE_API_URL` 配置）。

### 后端开发

```bash
cd backend
# 配置环境：复制 conf/env.example.py → conf/env.py，修改数据库/Redis 连接信息

uv run python manage.py runserver 0.0.0.0:8000     # Django 开发服务器
# 或 ASGI 模式（支持 WebSocket）
uv run uvicorn application.asgi:application --port 8000 --host 0.0.0.0 --workers 8
```

访问 Swagger 文档: `http://localhost:8000/`，ReDoc: `http://localhost:8000/redoc/`。

### MCP Server 开发

```bash
cd cloudweave-mcp
uv run python server.py    # 启动 MCP Server（stdio 模式）
```

i18n 翻译编译：

```bash
cd backend
# 生成 .po 翻译文件
uv run python manage.py makemessages -l en -l zh-hant
# 编译 .po 为 .mo
uv run python manage.py compilemessages -l en -l zh-hant
```

### 代码生成

```bash
# 从数据库表自动生成 FastCrud 前端页面
bash crud-gen.sh <app_name> <view_name> <table_name>
# 示例: bash crud-gen.sh system my_view my_table
```

### 测试

```bash
cd backend
uv run pytest                    # 运行所有测试
uv run pytest dvadmin/system/tests/  # 运行单个 app 测试
```

---

## 架构概览

### 整体请求流

```
                  ┌─────────────────────────────┐
                  │      AI 客户端 (外部)        │
                  │  Claude Desktop / CodeBuddy  │
                  └──────────────┬──────────────┘
                                 │ MCP Protocol (stdio / HTTP+SSE)
                  ┌──────────────▼──────────────┐
                  │    织云 MCP Server           │
                  │    (cloudweave-mcp)          │
                  │    Tool 注册 & 调用转发       │
                  └──────────────┬──────────────┘
                                 │ 内部 HTTP 调用 DRF API
浏览器 → Nginx (:8080) → /mcp/* → MCP Server
                       → /api/* 代理到 Django (:8000)
                       → /* 返回前端 SPA 静态资源
Django → PostgreSQL (:5432) / Redis (:6379) / Celery Worker
WebSocket → Django Channels → 实时消息推送
```

### 后端架构 (`backend/`)

```
backend/
├── application/          # Django 项目配置
│   ├── settings.py       # 核心配置：DB、DRF、JWT、中间件、Channels、插件
│   ├── urls.py           # 根路由：/api/system/、/api/login/、Swagger、SSE
│   └── asgi.py           # ASGI 入口（HTTP + WebSocket 协议路由）
├── conf/env.py           # 环境配置：数据库、Redis、DEBUG、ALLOWED_HOSTS（gitignore）
├── dvadmin/
│   ├── system/           # 核心系统 App（RBAC 用户/角色/菜单/部门/字典/区域/文件/日志）
│   ├── test_app/         # 示例 App（Blog、Product 模型）
│   └── utils/            # 共享工具（自定义后端认证、序列化器、中间件、权限）
├── plugins/              # 插件目录（如 dvadmin3-celery）
├── util/                 # 额外工具
├── locale/               # i18n 翻译文件 (.po/.mo)
├── templates/web/        # 生产环境前端 SPA 构建产物（Nginx 反向代理到这里）
└── manage.py             # Django 管理入口
```

#### Django 核心 App: `dvadmin.system`

该系统 App 是整个 RBAC 权限模型的核心，包含以下模型：

- **Users** (`AUTH_USER_MODEL`) — 自定义用户模型，替换 Django 默认 User
- **Role / Dept** — 角色和部门，支持按部门划分数据权限范围
- **Menu / MenuButton** — 动态菜单和按钮权限标识，权限粒度细分到每个按钮和每列
- **Dictionary** — 系统字典数据缓存
- **Area** — 省市县区域数据
- **FileList** — 统一文件/附件管理
- **LoginLog / OperationLog** — 登录和操作日志
- **SystemConfig** — 系统配置（前端可动态读取，如登录页配置）
- **MessageCenter / MessageTargetUser** — 消息中心（支持 SSE 实时推送）

#### 认证与权限

- **JWT 认证**: `djangorestframework-simplejwt`，访问令牌有效期 1440 分钟，通过 `Authorization: JWT <token>` 头传递
- **自定义认证后端**: `dvadmin.utils.backends.CustomBackend`，支持 MD5 密码哈希
- **列级权限**: 通过 `ColumnPermission` 控制接口响应中每个字段的可见性
- **接口白名单**: `/api/system/white/` 配置无需权限校验的 API
- **验证码**: `django-simple-captcha` 数学验证码，可配置关闭（`LOGIN_NO_CAPTCHA_AUTH=True`）
- **API 权限自动扫描**: 选中菜单 → 选择 Django app → 自动扫描 ViewSet 接口（`inspect.getmembers` + `pkgutil.iterModules`），批量生成 `MenuButton` 权限记录。前端按 Model → CRUD 语义两级分组展示（查询/新增修改/删除/其他颜色区分），详见 `docs/auto-permission-scan.md`

#### 中间件栈（按顺序）

`HealthCheckMiddleware` → `SecurityMiddleware` → `WhiteNoiseMiddleware` → `SessionMiddleware` → `CorsMiddleware` → 自定义 `LocaleMiddleware` → `CommonMiddleware` → `CsrfViewMiddleware` → `AuthenticationMiddleware` → `MessageMiddleware` → `XFrameOptionsMiddleware` → `ApiLoggingMiddleware`

#### 插件系统

后端通过 `settings.PLUGINS_URL_PATTERNS` 动态加载 `plugins/` 目录下的 Django App，支持 URL 路由、INSTALLED_APPS 和数据库迁移的自动注册。

### MCP Server 架构 (`cloudweave-mcp/`)

MCP Server 是独立进程，将 CloudWeave 全部业务能力抽象为标准化的 MCP Tool，供 Claude Desktop、CodeBuddy 等 AI 客户端调用，实现自然语言运维交互。

- **传输方式**: 本地开发用 stdio（零网络配置），团队部署用 HTTP+SSE
- **与后端集成**: MCP Server 通过内部 HTTP 调用复用 DRF Service 层，与 Django 解耦，不侵入核心业务代码
- **安全模型**: API Key 权限分级——可精确控制哪些客户端只能查询、哪些可以执行写操作
- **Tool 定义**: 使用 JSON Schema 标准化参数，AI 模型可自动理解并生成正确的调用参数
- **生态兼容**: 同一套 MCP Tool 可同时被 Claude、GPT、Gemini 等多个模型调用，不绑定特定供应商

### 前端架构 (`web/`)

```
web/src/
├── main.ts               # 入口：注册 Pinia/Router/ElementPlus/i18n/FastCrud/VXETable
├── App.vue               # 根组件：锁屏、主题设置、WebSocket 初始化
├── settings.ts           # FastCrud 全局 CRUD 配置
├── api/                  # API 接口层（login、menu）
├── components/           # 38+ 可复用业务组件（权限选择器、文件上传、富文本、图标选择等）
├── directive/            # 自定义指令：v-auth（按钮权限）、v-waves、v-drag
├── i18n/                 # 国际化（96 文件）：vue-i18n + Element Plus + FastCrud 三合一
├── layout/               # 布局系统（4 种布局：classic/columns/transverse/defaults）
├── router/               # 路由（双模式：后端动态路由 / 前端静态路由）
├── stores/               # Pinia 状态管理（17 个 Store）
│   ├── userInfo.ts       #   用户信息（角色、部门、头像）
│   ├── themeConfig.ts    #   主题/布局配置（49 项，LocalStorage 持久化）
│   ├── frontendMenu.ts   #   后端菜单 → 前端路由格式转换
│   ├── routesList.ts     #   当前路由列表
│   ├── dictionary.ts     #   字典缓存
│   ├── btnPermission.ts  #   按钮权限标识
│   └── ...
├── types/                # TypeScript 类型声明
├── utils/                # 25+ 工具函数
│   ├── service.ts        #   主 Axios 实例（完整错误处理、租户域名支持）
│   ├── request.ts        #   轻量 Axios 实例（登录/登出用）
│   ├── websocket.ts      #   WebSocket 客户端（心跳+自动重连）
│   └── commonCrud.ts     #   FastCrud 通用字段配置
└── views/                # 页面视图
    ├── system/           #   系统管理：home/login/user/role/menu/dept/areas/config/dictionary/
    │                     #   columns/fileList/downloadCenter/messageCenter/personal/log/whiteList/demo/error
    ├── celery/           #   Celery 任务管理（task/taskLog）
    ├── template/         #   代码生成模板（crud-gen.sh 使用）
    └── plugins/          #   插件页面自动扫描注册
```

#### 路由双模式

由 `themeConfig.isRequestRoutes` 控制：

1. **后端控制路由**（默认 `true`）：前端请求 `/api/system/menu/web_router/` → 后端返回 JSON 菜单树 → 转换为 Vue Router 动态添加。组件路径通过 `import.meta.glob` 动态匹配 `.vue/.tsx` 文件，支持目录/外链/内嵌等菜单类型。语言切换时自动重新获取菜单。

2. **前端控制路由**（`false`）：路由在 `router/route.ts` 的 `dynamicRoutes` 中硬编码，通过 `meta.roles` 与用户角色比对过滤。

#### API 层

两套 Axios 实例均在请求拦截器中自动附加 `Authorization: JWT <token>` 和 `Accept-Language` 头：

- **`utils/service.ts`** — 主请求层，用于所有业务 CRUD。响应 `code === 2000` 表示成功，完整处理 400/401/403/404/500 等 HTTP 状态码。
- **`utils/request.ts`** — 轻量层，用于登录/登出。响应 code 401 时清除缓存并跳转登录页。

FastCrud 通过 `settings.ts` 中的 `transformQuery` / `transformRes` 统一适配后端分页格式（`page`/`limit`/`ordering`）。

#### WebSocket 实时通信

在 `App.vue` 中初始化，连接 `ws://host/ws/<token>/`，2 秒心跳 + 最多 3 次自动重连。消息通过 `mittBus` 事件总线分发，支持 SYSTEM（系统通知）和 Content（业务弹窗确认）两种类型。

#### i18n 国际化

前后端均支持多语言（zh-cn / en / zh-tw），详见 `docs/i18n-guide.md`。

- **前端**: `web/src/i18n/` 下 `lang/`（全局）+ `pages/`（页面级）按模块拆分翻译文件。`i18n/index.ts` 使用 `import.meta.glob` 自动扫描合并，无需手动 import。vue-i18n 9.x + Element Plus i18n + FastCrud i18n 三合一
- **后端**: Django gettext 国际化，`.po/.mo` 文件位于 `locale/` 目录。菜单/按钮多语言名称通过数据库字段存储（`name_en`/`name_zh_tw`）
- **语言切换**: 前端切换时自动更新 Cookie `django_language`，触发后端重新获取含对应语言的菜单 JSON

### PRD 演进方向

根据 `docs/运维管理系统_PRD_v2.md` v1.4，CloudWeave 共规划 **9 大功能模块**：

| 模块 | 核心能力 |
|------|----------|
| 资产管理 | 项目、服务器、域名、IP、端口的 CRUD 管理，支持批量导入和冲突检测 |
| 关联关系管理 | 项目→服务器→IP→域名→端口的全链路多对多关系，支持影响范围分析 |
| ICP 备案管理 | 备案登记、变更留痕、到期提醒，全生命周期合规追溯 |
| 云平台管理 | 多云账号/注册商/域名注册账户的统一纳管 |
| 云 API 集成 | 多云 OpenAPI 对接：资产同步、余额同步、余额告警、到期通知 |
| 办公资产管理 | 电脑/手机/SIM卡/平板等设备全生命周期：资产类型自定义、借用归还审批、主体归属/调拨、手机卡实名制、报废管理、多维报表 |
| AI 智能集成 (MCP) | cloudweave-mcp Server 将全部业务能力暴露为 AI Tool，支持自然语言查询与操作 |
| 可视化拓扑 | 力导向图展示资源关联链路，500 节点内性能优秀 |
| 系统管理 | RBAC 用户/角色/权限/日志，继承自 django-vue3-admin 基座 |

**Django App 设计原则**：每个 App 职责单一，仅通过 Service 层交互，避免跨 App 直接调用 Model；所有业务逻辑下沉至 `services.py`，View 层仅做参数校验与响应组装；API 版本通过 URL 前缀管理（`/api/v1/`、`/api/v2/`）。

**前端设计原则**：目录按功能模块划分（`views/assets/`、`views/cloud/` 等），禁止按文件类型平铺；组件分层——通用 UI → 业务组件 → 页面组件，下层不引用上层；API 层 `api/` 目录按模块拆分，统一管理请求路径与类型。

---

## 关键约定

- **数据库表前缀**: `dvadmin_`（在 `conf/env.py` 的 `TABLE_PREFIX` 中配置）
- **自定义用户模型**: `AUTH_USER_MODEL = "system.Users"`
- **API 响应格式**: 统一 `{ code: 2000, data: ..., message: "success" }`（后端）/ 前端 service.ts 将 code 2000 视为成功
- **前端文件命名**: Vue 组件 PascalCase，工具函数 camelCase，Store 分隔用 camelCase
- **权限模型**: RBAC，权限粒度三级——菜单级 > 按钮级 > 列级
- **默认超级管理员**: `superadmin` / `admin123456`
