# 织云 (CloudWeave) — 综合运维管理系统 PRD

---

## 文档信息

| 字段 | 内容 |
|---|---|
| 文档名称 | 织云 (CloudWeave) — 综合运维管理系统产品需求文档 |
| 文档版本 | v1.2 |
| 创建日期 | 2026-06-29 |
| 更新日期 | 2026-06-29 |
| 架构模式 | 前后端分离：Django REST Framework (后端) + Vue 3 (前端) |
| 目标技术栈 | Python 3.12+ / Django 5.x / DRF / Vue 3 / PostgreSQL 16 / Redis / Celery / Docker |
| 文档状态 | 已更新 |

### 变更记录

| 版本 | 日期 | 变更内容 |
|---|---|---|
| v1.0 | 2026-06-29 | 初稿，涵盖 6 大核心模块 |
| v1.1 | 2026-06-29 | 新增"云平台 API 集成"模块：服务器资产同步、余额同步、余额告警、到期通知 |
| v1.2 | 2026-06-29 | 新增技术选型章节；架构调整为前后端分离（DRF + Vue 3） |

---

## 项目标识

| 字段 | 内容 |
|---|---|
| 项目名称 | **织云 (CloudWeave)** |
| 标语 | **织就云上脉络，洞见资产关联** |
| 项目代号 | cloudweave |

---

## 技术选型

### 0.1 架构概述

系统采用**前后端完全分离**架构，后端提供 RESTful API，前端为独立 SPA 应用，通过 HTTP/HTTPS + JWT Token 鉴权通信。两者可独立开发、独立构建、独立部署，通过 Nginx 反向代理统一对外提供服务。

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (反向代理)                       │
│              /api/* → 后端    /* → 前端静态资源               │
└──────────┬──────────────────────────────────┬───────────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────────┐          ┌──────────────────────────┐
│   前端 (SPA)         │  HTTP    │   后端 (Django REST)      │
│   Vue 3 + Vite      │◀────────▶│   DRF + Celery            │
│   TypeScript        │  JWT     │   Python 3.12+            │
│   Pinia / Vue Router│          │                           │
└─────────────────────┘          └──────────┬────────────────┘
                                            │
                          ┌─────────────────┼─────────────────┐
                          ▼                 ▼                  ▼
                   ┌──────────┐     ┌──────────┐      ┌──────────┐
                   │PostgreSQL│     │  Redis   │      │  Celery  │
                   │  16      │     │ 缓存/队列 │      │  Worker  │
                   └──────────┘     └──────────┘      └──────────┘
```

### 0.2 后端技术栈

| 层级 | 技术 | 版本 | 用途 |
|---|---|---|---|
| 语言 | Python | 3.12+ | 主力开发语言 |
| Web 框架 | Django | 5.x LTS | 核心框架，ORM、Admin、中间件 |
| API 框架 | Django REST Framework | 3.15+ | RESTful API 构建，序列化、视图集、权限、限流 |
| API 文档 | drf-spectacular | — | OpenAPI 3.0 自动生成，Swagger UI / ReDoc 交互式文档 |
| 认证 | djangorestframework-simplejwt | — | JWT 令牌签发、刷新、黑名单 |
| 数据库 | PostgreSQL | 16+ | 主数据库，JSONB / 全文检索 / 窗口函数 |
| 数据库驱动 | psycopg2 (binary) | — | PostgreSQL Python 驱动，性能最佳 |
| 缓存 | Redis | 7.x | 会话缓存、API 限流计数、Celery 消息代理 |
| 异步任务 | Celery | 5.x | 定时同步调度、告警扫描、邮件发送等后台任务 |
| 定时调度 | django-celery-beat | — | 基于 Django 数据库的 Periodic Task 调度 |
| 实时通信 | Django Channels | 4.x | WebSocket 支持，告警实时推送 |
| WebSocket | Daphne / Uvicorn | — | ASGI 服务器 |
| 加密 | cryptography (Fernet) | — | API 密钥 AES-256 加密 |
| 云 SDK | tencentcloud-sdk-python / aliyun-python-sdk / huaweicloud-sdk-python | — | 多云平台 API 调用 |
| 任务队列 | Celery + Redis | — | 同步任务异步化，避免阻塞 API 响应 |
| 部署 | Docker + Gunicorn/Daphne | — | 容器化部署 |

**Django App 设计原则**：
- 每个 App 职责单一，仅通过 Service 层交互，避免跨 App 直接调用 Model
- 所有业务逻辑下沉至 `services.py`，View 层仅做参数校验与响应组装
- API 版本通过 URL 前缀管理：`/api/v1/`、`/api/v2/`

### 0.3 前端技术栈

| 层级 | 技术 | 版本 | 用途 |
|---|---|---|---|
| 框架 | Vue | 3.5+ (Composition API) | 核心前端框架 |
| 构建工具 | Vite | 6.x | 开发服务器、HMR、生产构建 |
| 语言 | TypeScript | 5.x | 类型安全，提升代码可维护性 |
| 状态管理 | Pinia | 2.x | 全局状态管理，替代 Vuex |
| 路由 | Vue Router | 4.x | SPA 路由管理 |
| HTTP 客户端 | Axios | — | API 请求、拦截器（Token 自动刷新） |
| UI 组件库 | Element Plus | 2.x | 企业级中后台 UI 组件（表格/表单/Dialog/抽屉等） |
| CSS 方案 | Tailwind CSS | 4.x | 原子化 CSS，快速定制样式 |
| 可视化拓扑 | vis-network (vis.js) | — | 力导向图，适合 500 节点以内的运维资源拓扑 |
| 图表 | ECharts | 5.x | 余额趋势图、备案状态分布饼图、告警统计等 |
| 图标 | @element-plus/icons-vue | — | Element Plus 配套图标 |
| 表格增强 | vxe-table | — | 虚拟滚动、可编辑表格（大数据量列表场景） |
| 代码规范 | ESLint + Prettier | — | 代码格式与质量 |
| 包管理 | pnpm | — | 高效、磁盘友好的包管理器 |

**前端架构设计原则**：
- **目录按功能模块划分**：`views/assets/`、`views/cloud/`、`views/alerts/`、`views/topology/` 等，禁止按文件类型平铺
- **组件分层**：通用 UI 组件 → 业务组件 → 页面组件，下层不能引用上层
- **API 层统一封装**：`api/` 目录下按模块拆分，统一管理请求路径、参数类型、响应类型
- **路由守卫**：前置守卫检查 Token 有效性，无权限页面统一拦截跳转 403

### 0.4 基础设施

| 类别 | 技术 | 说明 |
|---|---|---|
| 容器化 | Docker + Docker Compose | 本地开发与生产部署一体化 |
| Web 服务器 | Nginx | 反向代理、静态资源分发、SSL 终结 |
| CI/CD | GitHub Actions / 工蜂 CI | 自动测试、构建、部署 |
| 监控 | Sentry | 前后端错误追踪 |
| 日志 | Django Logging → file / ELK | 结构化日志输出 |
| 版本控制 | Git | 主干开发 + feature 分支 |

### 0.5 选型理由

**为什么前后端分离？**
- 后端只负责数据和业务逻辑，前端独立迭代 UI 交互，互不阻塞
- 拓扑可视化（vis-network）、图表（ECharts）等重前端功能更适合 SPA 架构
- 未来可扩展移动端或小程序，复用同一套 API
- 前后端各自独立测试、独立部署，CI/CD 流水线分工明确

**为什么 Vue 3 而非 React？**
- Vue 3 Composition API + `<script setup>` 语法简洁，学习曲线平缓，适合团队快速上手
- Element Plus 提供开箱即用的中后台组件（Table/Form/Dialog/抽屉），显著减少重复造轮子
- 与 Django 社区的 Vue-DRF 组合方案成熟，生态配套完善

**为什么选择 PostgreSQL？**
- JSONB 类型支持索引和高效查询，远优于 MySQL 的 JSON 存储，非常适合 `extra_data`、`condition_config` 等半结构化字段
- 原生支持 `ArrayField`、`HStoreField`、`DateRangeField` 等 Django 高级字段类型，无需额外插件
- 窗口函数、CTE（WITH 子句）在处理关联追溯和趋势分析等复杂查询时表达能力更强
- Django ORM 对 PostgreSQL 的支持最为完整（`django.contrib.postgres` 提供专属字段和索引）
- 严格的 SQL 标准遵循和 ACID 特性，适合需要审计追溯的运维数据场景

**为什么 vis-network 而非 D3.js / AntV G6？**
- vis-network 配置式 API 简洁，30 行代码即可渲染力导向图
- 物理引擎稳定，500 节点以内性能表现优秀
- ECharts 补充图表需求，与 vis-network 各司其职

---

## 一、产品概述

### 1.1 产品定位

面向中小型团队的综合运维资源管理平台，以**资源关联拓扑**为核心设计理念，实现服务器资产、项目、域名、IP、端口等多维资源的统一登记、关联追踪、变更审计与可视化展示。

### 1.2 核心价值

- **"一图胜千言"**：通过拓扑视图从任意资源节点出发，直观追溯其上下游完整关联链路，告别"这个 IP 是谁的？这个域名解析到哪台机器？"的运维黑洞。
- **"关联即真相"**：建立项目 → 服务器 → IP → 域名 → 端口的全链路模型，任何一个节点下线或变更时，系统可快速评估影响范围。
- **"合规可追溯"**：ICP 备案全生命周期管理，备案主体变更留痕，方便合规审计。
- **"API 驱动运维"**：对接主流云平台 OpenAPI，自动同步服务器资产、账户余额，余额不足或资源到期时主动告警，减少人工巡检成本。

### 1.3 目标用户

| 角色 | 职责 | 关注点 |
|---|---|---|
| 运维工程师 | 日常资源管理与维护 | 资源登记、关联配置、拓扑探索、云 API 同步 |
| 项目经理/技术负责人 | 项目资源盘点 | 项目关联的资源总览、成本归属 |
| 财务/成本管理员 | 云账户成本管控 | 余额监控、费用趋势、余额告警 |
| 合规/安全管理员 | 备案合规审计 | ICP 备案状态、备案变更历史 |
| 系统管理员 | 平台运维 | 用户权限、操作日志 |

---

## 二、功能模块划分

本系统共划分为 **7 大功能模块**：

```
┌───────────────────────────────────────────────────────────────────┐
│                         综合运维管理系统                            │
├────────┬────────┬────────┬────────┬────────┬──────────┬──────────┤
│ 资产   │ 关联   │ ICP    │ 云平台 │ 云API  │ 可视化   │ 系统     │
│ 管理   │ 关系   │ 备案   │ 管理   │ 集成   │ 拓扑     │ 管理     │
│ 模块   │ 管理   │ 管理   │        │        │          │          │
├────────┼────────┼────────┼────────┼────────┼──────────┼──────────┤
│· 项目  │· 配置  │· 备案  │· 云平台│· API   │· 拓扑图  │· 用户    │
│· 服务器│· 查询  │  登记  │  账号  │  凭证  │· 节点    │· 角色    │
│· 域名  │· 影响  │· 备案  │· 注册商│  配置  │  探索    │· 权限    │
│· IP    │  分析  │  变更  │· 域名  │· 资产  │· 导出    │· 日志    │
│· 端口  │        │· 变更  │  注册  │  同步  │          │          │
│        │        │  历史  │  账户  │· 余额  │          │          │
│        │        │· 到期  │        │  同步  │          │          │
│        │        │  提醒  │        │· 告警  │          │          │
│        │        │        │        │  规则  │          │          │
│        │        │        │        │· 告警  │          │          │
│        │        │        │        │  通知  │          │          │
└────────┴────────┴────────┴────────┴────────┴──────────┴──────────┘
```

### 2.1 资产管理模块

**目标**：对项目、服务器、域名、IP、端口五类核心资源进行 CRUD 管理，每类资源作为独立实体存在。

#### 2.1.1 项目管理

| 功能点 | 说明 |
|---|---|
| 项目列表 | 分页展示、支持按名称/状态/负责人搜索筛选 |
| 项目详情 | 展示项目基本信息 + 关联的服务器/域名/端口汇总卡片 |
| 新增/编辑项目 | 名称、描述、负责人、状态（运行中/已下线/维护中）、所属团队/部门 |
| 删除项目 | 软删除，保留历史关联记录 |
| 资源概览卡片 | 在详情页以卡片形式展示该项目下关联的服务器数、域名数、端口数 |

#### 2.1.2 服务器管理

| 功能点 | 说明 |
|---|---|
| 服务器列表 | 展示主机名、IP、云平台、操作系统、状态，支持多条件筛选 |
| 服务器详情 | 基本信息 + 关联项目列表 + 网络接口（多IP） + 开放端口列表 + 部署的域名 |
| 新增/编辑服务器 | 主机名、操作系统、CPU/内存/磁盘规格、SSH 端口、登录方式、所属云平台、到期时间、备注 |
| 批量导入 | 支持 CSV/Excel 批量导入服务器信息 |
| 状态标记 | 运行中 / 已关机 / 已销毁 / 维护中 |

#### 2.1.3 域名管理

| 功能点 | 说明 |
|---|---|
| 域名列表 | 展示域名、注册商、ICP备案状态、解析IP数、关联项目、到期时间 |
| 域名详情 | 基本信息 + 解析记录（A记录/CNAME等）+ 关联项目 + ICP备案信息卡片 + 变更历史时间线 |
| 新增/编辑域名 | 域名、注册商、注册日期、到期日期、DNS 服务商、备注 |
| 到期提醒 | 域名到期前 30/15/7 天站内通知（或对接邮件/企业微信通知） |

#### 2.1.4 IP 管理

| 功能点 | 说明 |
|---|---|
| IP 列表 | 展示 IP 地址、类型（公网/内网）、归属服务器、关联域名列表 |
| IP 详情 | 基本信息 + 归属服务器 + 解析至该 IP 的域名列表 + 开放端口 |
| 新增/编辑 IP | IP 地址、类型（公网/内网/弹性IP）、归属服务器、运营商、备注 |
| 冲突检测 | 新增 IP 时检测是否已被其他服务器占用 |
| 批量导入 | 支持 CIDR 网段批量录入内网 IP |

#### 2.1.5 端口管理

| 功能点 | 说明 |
|---|---|
| 端口列表 | 展示端口号、协议、所属服务器/IP、服务名称、关联项目 |
| 端口详情 | 基本信息 + 所属服务器信息 + 关联项目 |
| 新增/编辑端口 | 端口号、协议(TCP/UDP)、服务名称(如 nginx/mysql/redis)、所属服务器、关联 IP、备注 |
| 端口冲突检测 | 同一服务器+IP 下不允许相同端口号+协议重复 |

### 2.2 关联关系管理模块

**目标**：建立并维护五类资源之间的多对多关联关系，支持从任意节点追溯完整关联链路。

#### 2.2.1 关联关系模型

```
                    ┌──────────┐
                    │   项目    │
                    │ Project  │
                    └────┬─────┘
                         │ 部署于 (deploy_on)
                         │ 多对多
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ 服务器A  │ │ 服务器B  │ │ 服务器C  │
         │ Server  │ │ Server  │ │ Server  │
         └────┬────┘ └────┬────┘ └────┬────┘
              │ 拥有 (has_ip)         │
              │ 一对多                │
              ▼                      ▼
         ┌─────────┐           ┌─────────┐
         │  IP 1   │           │  IP 2   │
         │(公网)   │           │(内网)   │
         └────┬────┘           └─────────┘
              │ 解析至 (resolves_to)
              │ 多对多
              ▼
         ┌─────────┐
         │ 域名 A   │
         │ Domain  │
         └────┬────┘
              │ 关联项目 (related_project)
              │ 多对多
              ▼
         ┌──────────┐
         │   项目    │
         │ Project  │
         └──────────┘

端口 (Port) 依附于 服务器 + IP 的组合上
         ┌─────────┐
         │ 服务器   │─── 开放端口 (opens_port) ───▶  Port (8080/TCP/nginx)
         │ Server  │─── 开放端口 (opens_port) ───▶  Port (3306/TCP/mysql)
         └─────────┘
```

#### 2.2.2 关联配置功能

| 功能点 | 说明 |
|---|---|
| 项目关联服务器 | 在项目详情页/服务器详情页双向添加/解除关联，选择部署环境标签（生产/测试/预发布） |
| 域名关联 IP | 在域名详情页添加 DNS 解析记录，选择记录类型(A/CNAME)，绑定目标 IP；系统自动建立域名与 IP 的关联 |
| 域名关联项目 | 标记域名所服务的项目，支持一个域名关联多个项目（如泛域名下多个子项目） |
| 服务器添加 IP | 在服务器详情页管理网络接口，添加/移除 IP |
| 服务器添加端口 | 在服务器详情页或 IP 详情页管理开放端口 |
| 端口关联项目 | 标记端口所服务的具体项目 |
| 快速关联向导 | 提供一个向导式界面，从项目出发一次性完成：选择服务器 → 配置 IP → 添加域名解析 → 配置端口 |

#### 2.2.3 关联查询与影响分析

| 功能点 | 说明 |
|---|---|
| 上游追溯 | 从域名出发，查看解析至哪些 IP → 哪些服务器 → 哪些项目 |
| 下游追溯 | 从项目出发，查看部署在哪些服务器 → 有哪些 IP → 解析了哪些域名 → 开放了哪些端口 |
| 影响分析报告 | 当标记某服务器为"维护中"或"已下线"时，系统列出受影响的项目、域名、端口清单 |
| 关联完整性检查 | 检测未关联项目的服务器、未配置解析的域名等"孤儿"资源 |

### 2.3 ICP 备案管理模块

#### 2.3.1 备案信息登记

| 功能点 | 说明 |
|---|---|
| 备案状态标记 | 每个域名支持标记：未备案 / 已备案 / 备案中 / 备案注销 / 无需备案（境外域名） |
| 备案信息录入 | 备案号（如 京ICP备XXXXXXXX号）、主办单位名称、主办单位性质（企业/个人/政府机关等）、负责人姓名、负责人联系电话、负责人邮箱、审核通过日期 |
| 备案信息与域名关联 | 一条域名记录关联一条备案信息（一对一）；如果一个备案号对应多个域名，可在每个域名下分别关联同一备案主体 |

#### 2.3.2 备案变更流程

```
发起变更申请 ──▶ 填写变更内容 ──▶ 提交审核 ──▶ 审核通过 ──▶ 更新备案信息
                    │                              │
                    └── 保存草稿                    └── 记录变更历史
```

- **变更内容**：支持对主办单位、负责人、联系电话、邮箱等备案主体信息的变更
- **变更审核**：需要具有备案管理权限的用户进行审核确认
- **变更历史**：每次变更记录完整的 Before/After 快照，形成变更时间线

#### 2.3.3 变更历史

| 功能点 | 说明 |
|---|---|
| 变更时间线 | 在域名详情页以时间线形式展示该域名所有备案变更记录 |
| 变更详情 | 每条记录展示：变更时间、操作人、变更字段、变更前值、变更后值、审核状态 |
| 变更对比 | 支持选中两条变更记录进行 Diff 对比 |
| 导出 | 支持导出域名的备案变更历史为 PDF/Excel |

#### 2.3.4 备案到期提醒

- 备案审核通过后，部分省份要求定期复核
- 系统支持设置备案复核提醒日期，到期前通知

### 2.4 云平台归属管理模块

**目标**：统一管理企业使用的云平台账号与域名注册商信息，并存储 API 凭证以支持后续自动同步和告警。

#### 2.4.1 云平台账号管理

| 功能点 | 说明 |
|---|---|
| 云平台账号列表 | 展示所有云平台账号：平台名称、账号别名、账号 ID、联系人、API 接入状态、最近同步时间 |
| 新增/编辑账号 | 平台名称（腾讯云/阿里云/华为云/AWS/Azure/私有化）、账号别名、账号 ID/UIN、联系人 |
| API 凭证管理 | 为每个云平台账号配置 API 密钥（SecretId/SecretKey），密钥加密存储，支持测试连通性 |
| 同步地域配置 | 选择需要同步的地域列表（如 ap-guangzhou / ap-shanghai / ap-beijing），支持多地域勾选 |
| 同步范围配置 | 勾选需要同步的服务：云服务器(CVM/ECS)、余额查询(Billing) |
| 账号删除 | 删除前需确认无关联的服务器资源，删除后对应的 API 凭证一并清除 |

#### 2.4.2 域名注册商管理

| 功能点 | 说明 |
|---|---|
| 注册商列表 | 展示注册商名称、注册账户别名、联系人 |
| 新增/编辑注册商 | 注册商名称（腾讯云/阿里云/美橙/易名/GoDaddy 等）、注册账户别名、注册账户 ID、联系人 |
| 服务器云平台标注 | 每台服务器标注所属云平台以及实例 ID |
| 域名注册商标注 | 每个域名标注注册商以及注册账户 |

#### 2.4.3 账号关联

| 功能点 | 说明 |
|---|---|
| 服务器关联云账号 | 服务器所属云平台账号关联，方便成本归属和账单核对 |
| 域名关联注册账户 | 域名注册账户关联 |
| 账号资源总览 | 在云账号详情页汇总展示该账号下的所有服务器数量、余额信息、最近同步状态 |

### 2.5 可视化拓扑模块

#### 2.5.1 拓扑图展示

- 以**力导向图（Force-Directed Graph）** 形式展示资源及其关联关系
- 不同资源类型使用不同颜色和图标区分：

| 资源类型 | 颜色 | 图标/形状 |
|---|---|---|
| 项目 (Project) | 蓝色 | 圆形 |
| 服务器 (Server) | 绿色 | 矩形 |
| IP 地址 (IP) | 橙色 | 菱形 |
| 域名 (Domain) | 紫色 | 六边形 |
| 端口 (Port) | 灰色 | 小圆点 |

- 连线表示关联关系，不同类型连线使用不同样式：

| 关联关系 | 连线样式 | 说明 |
|---|---|---|
| 项目 → 服务器 | 蓝色实线 | "部署于" |
| 服务器 → IP | 绿色实线 | "拥有" |
| IP → 域名 | 紫色虚线 | "解析至" |
| 域名 → 项目 | 橙色虚线 | "服务于" |
| 服务器 → 端口 | 灰色实线 | "开放" |

#### 2.5.2 交互功能

| 功能点 | 说明 |
|---|---|
| 节点点击展开 | 点击任意节点，弹出侧边抽屉/dialog 展示该节点的详细信息卡片和关联资源列表；拓扑图中同时高亮该节点的一度关联节点 |
| 节点聚焦/展开 | 双击节点可将其设为中心焦点，拓扑图重新布局以该节点为中心展示其上下游 |
| 拖拽与缩放 | 支持鼠标拖拽节点、滚轮缩放、平移画布 |
| 搜索定位 | 顶部搜索框输入资源名称/IP/域名，拓扑图中高亮定位对应节点并自动聚焦 |
| 筛选过滤 | 按资源类型勾选显示/隐藏，按项目筛选仅展示某项目关联链路 |
| 视图保存 | 保存当前拓扑视图布局，下次打开恢复 |
| 全屏模式 | 支持全屏查看拓扑图 |
| 导出 | 导出当前拓扑图为 PNG/SVG 图片 |

#### 2.5.3 拓扑导航路径示例

**场景**：用户查看域名 `api.example.com` 的完整上下游链路。

```
域名 api.example.com
  │
  ├── 解析至 ──▶ IP: 123.45.67.89 (公网)
  │                  │
  │                  └── 归属服务器 ──▶ server-web-01 (腾讯云 CVM)
  │                                        │
  │                                        ├── 部署项目 ──▶ 电商平台-API服务
  │                                        │
  │                                        └── 开放端口 ──▶ 443/TCP (nginx)
  │                                                     ──▶ 8080/TCP (tomcat)
  │
  └── ICP备案 ──▶ 京ICP备2024XXXXXX号
                   主办单位: XX科技有限公司
                   负责人: 张三
```

### 2.6 系统管理模块

| 功能点 | 说明 |
|---|---|
| 用户管理 | 用户 CRUD、绑定角色 |
| 角色管理 | 预置角色：超级管理员、运维管理员、只读用户；支持自定义角色 |
| 权限控制 | 基于 Django 权限系统的功能级权限（查看/新增/编辑/删除）+ 数据级权限（按项目/团队隔离） |
| 操作日志 | 记录所有资源的增删改操作：操作人、操作时间、操作类型、操作对象、变更内容（JSON diff） |
| 登录日志 | 记录用户登录 IP、时间、登录结果 |

### 2.7 云平台 API 集成模块

**目标**：通过各云平台官方 OpenAPI，实现服务器资产的自动同步、账户余额的定时拉取，并结合告警规则引擎实现余额不足、资源到期、同步失败等场景的主动通知。

#### 2.7.1 API 同步架构

```
┌──────────────────────────────────────────────────────────┐
│                    综合运维管理系统                         │
│                                                          │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────┐  │
│  │ Celery Beat │──▶│ Sync Scheduler│──▶│  API Adapter  │  │
│  │ (定时调度)   │   │ (同步编排器)   │   │  (适配器层)    │  │
│  └─────────────┘   └──────┬───────┘   └───────┬───────┘  │
│                           │                    │          │
│                           ▼                    ▼          │
│                    ┌──────────────┐   ┌───────────────┐  │
│                    │  Sync Log    │   │ Cloud API SDK  │  │
│                    │  (同步日志)   │   │ · 腾讯云 SDK   │  │
│                    └──────────────┘   │ · 阿里云 SDK   │  │
│                                       │ · 华为云 SDK   │  │
│                                       │ · AWS SDK     │  │
│                                       └───────────────┘  │
│                                                          │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────┐  │
│  │ Alert Engine│◀──│ Rule Evaluator│◀──│Balance/Expire │  │
│  │ (告警引擎)   │   │ (规则求值器)   │   │ Data          │  │
│  └──────┬──────┘   └──────────────┘   └───────────────┘  │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────────────────────────┐    │
│  │  通知渠道: 站内消息 / 邮件 / 企业微信               │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

#### 2.7.2 API 凭证与同步配置

| 功能点 | 说明 |
|---|---|
| API 凭证配置 | 在云平台账号详情页配置 SecretId / SecretKey，密钥经 AES-256 加密存储于数据库，前端仅展示脱敏信息（如 `AKID****xyz`） |
| 连通性测试 | 配置凭证后提供"测试连接"按钮，调用云平台轻量 API（如查询地域列表）验证凭证有效性 |
| 同步地域选择 | 勾选需要纳入同步的地域列表（如 ap-guangzhou / ap-shanghai），可随时调整 |
| 同步服务开关 | 独立开关控制：CVM/ECS 资产同步、余额查询同步，可分别启用/停用 |
| 同步周期设置 | 支持手动触发 + 定时自动同步，默认每 6 小时执行一次全量同步，可自定义间隔 |
| 增量同步 | 记录上次同步时间戳，后续同步时仅拉取变更的实例，减少 API 调用量 |

#### 2.7.3 服务器资产同步

| 功能点 | 说明 |
|---|---|
| 实例拉取 | 调用云平台 DescribeInstances / DescribeInstances 等 API，拉取指定地域下的所有实例 |
| 字段映射 | 将云平台返回字段映射到系统 Server 模型：实例 ID → instance_id、实例名称 → hostname、操作系统 → os、CPU/内存 → cpu_cores/memory_gb、公网 IP → 自动创建 IP 记录、状态 → status、到期时间 → expire_date、可用区 → 存入 extra_data JSON 字段 |
| 差异对比 | 同步时将云端数据与本地数据库做 Diff：新增实例 → 自动创建 Server + IP 记录；已存在实例 → 更新属性（规格变更、IP 变更等）；云端已销毁实例 → 标记为 terminated 状态（不删除记录）|
| 同步日志 | 每次同步生成详细日志：同步时间、耗时、新增/更新/标记下线数量、失败项及错误原因 |
| 手动同步 | 在云平台账号详情页提供"立即同步"按钮，支持单账号按需触发 |

#### 2.7.4 账户余额同步

| 功能点 | 说明 |
|---|---|
| 余额查询 | 调用云平台 Billing API 查询账户余额信息，包括：可用现金余额、代金券余额、信用额度、冻结金额 |
| 余额记录 | 每次查询结果写入 `balance_record` 表，形成余额历史数据 |
| 余额趋势图 | 在仪表盘或云账号详情页展示余额变化折线图（近 30 天/90 天），直观展示账户消费趋势 |
| 多币种支持 | 支持人民币(CNY)、美元(USD) 等多币种余额记录，统一按查询当日汇率折算展示 |

#### 2.7.5 告警规则引擎

| 功能点 | 说明 |
|---|---|
| 规则列表 | 展示所有告警规则：规则名称、告警类型、告警级别、启用状态、上次触发时间 |
| 新增/编辑规则 | 规则名称、告警类型（余额阈值 / 资源到期 / 同步失败）、告警目标（指定云账号或全部）、触发条件、告警级别（严重/警告/提醒）、通知渠道、通知对象 |
| 余额告警规则 | 条件配置：当可用余额 ≤ X 元时触发告警，支持设置多级阈值（如余额 < 1000 元「警告」、余额 < 100 元「严重」）|
| 资源到期告警规则 | 条件配置：服务器/域名到期前 N 天触发告警（默认 30/15/7 天），可按云账号分组设置不同阈值 |
| 同步失败告警规则 | 条件配置：连续 N 次同步失败（或失败率超过 X%）时触发告警，防止凭证过期导致长期数据失真 |
| 规则启用/停用 | 支持临时关闭某条告警规则而不删除 |
| 通知渠道配置 | 每条规则可独立配置通知渠道：站内消息（默认开启）、邮件、企业微信（需预先配置 Webhook）|

#### 2.7.6 告警通知与处理

| 功能点 | 说明 |
|---|---|
| 告警记录列表 | 展示历史告警记录：告警标题、级别、触发时间、状态（已触发/已确认/已解决）|
| 告警详情 | 展示告警详情：触发条件、当前值 vs 阈值、涉及资源链接 |
| 告警确认 | 运维人员可"确认"告警（表示已知悉），记录确认人和时间 |
| 告警解决 | 问题处理后可标记为"已解决"，支持填写处理备注 |
| 告警收敛 | 同一规则在冷却期内（默认 2 小时）不重复发送通知，避免告警轰炸 |
| 通知模板 | 邮件/企业微信通知使用模板化格式：告警标题 + 详情摘要 + 操作链接 |
| 免打扰时段 | 支持配置免打扰时间窗口（如 22:00-08:00），时间段内告警不在即时渠道推送，仅记录待次日提醒 |

---

## 三、数据模型设计

### 3.1 实体关系总图 (ER Diagram)

```
┌──────────┐       ┌──────────────┐       ┌──────────┐
│  Project │       │ ProjectServer│       │  Server  │
│          │──M:N──│  (中间表)    │──M:N──│          │
│  id      │       │  environment │       │  id      │
│  name    │       │  project_id  │       │  hostname │
│  status  │       │  server_id   │       │  os      │
│  ...     │       └──────────────┘       │  ...     │
└────┬─────┘                              └────┬─────┘
     │                                         │ 1:N
     │ M:N                                     │
     │  ┌──────────────┐                       │
     ├──│ProjectDomain │                       ▼
     │  │  (中间表)    │                 ┌──────────┐
     │  └──────────────┘                 │    IP    │
     │         │                         │          │
     │         │ N:1                     │  id      │
     │         ▼                         │  address │
     │  ┌──────────┐                     │  type    │
     │  │  Domain  │                     │  server  │
     │  │          │                     │  ...     │
     │  │  id      │                     └────┬─────┘
     │  │  name    │                          │
     │  │  ...     │                          │ 1:N
     │  └────┬─────┘                          │
     │       │ M:N                            ▼
     │       │  ┌──────────────┐        ┌──────────┐
     │       └──│  DomainIP    │────────│   Port   │
     │          │  (中间表)    │        │          │
     │          │  record_type │        │  id      │
     │          │  domain_id   │        │  number  │
     │          │  ip_id       │        │  protocol│
     │          └──────────────┘        │  server  │
     │                                  │  ip      │
     │  ┌──────────────┐                │  project │
     └──│ ProjectPort  │────────────────│  ...     │
        │  (中间表)    │                └──────────┘
        └──────────────┘

┌──────────────┐     ┌──────────────────┐
│   Domain     │     │ IcpRecord        │
│              │1:1  │                  │
│   id ────────┼────▶│  id              │
│              │     │  domain_id (FK)  │
└──────────────┘     │  icp_number      │
                     │  company_name    │
                     │  ...             │
                     └────────┬─────────┘
                              │ 1:N
                              ▼
                     ┌──────────────────┐
                     │ IcpChangeLog     │
                     │                  │
                     │  icp_record_id   │
                     │  field_name      │
                     │  old_value       │
                     │  new_value       │
                     │  ...             │
                     └──────────────────┘

┌──────────┐     ┌──────────────────┐
│  Server  │     │ CloudPlatform    │
│          │N:1  │                  │
│  cloud_  │────▶│  id              │
│  platform│     │  name            │
│  ...     │     │  account_alias   │
└──────────┘     │  ...             │
                 └──────────────────┘

┌──────────┐     ┌──────────────────┐
│  Domain  │     │ Registrar        │
│          │N:1  │                  │
│  registrar────▶│  id              │
│  ...     │     │  name            │
└──────────┘     │  account_alias   │
                 │  ...             │
                 └──────────────────┘
```

### 3.2 核心实体表设计

#### 3.2.1 项目表 (project)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| name | CharField(200) | 是 | 项目名称，唯一 |
| slug | SlugField(200) | 是 | URL 友好的标识符 |
| description | TextField | 否 | 项目描述 |
| status | CharField(20) | 是 | 状态：running / offline / maintenance |
| owner | ForeignKey(User) | 是 | 项目负责人 |
| team | CharField(100) | 否 | 所属团队/部门 |
| created_at | DateTimeField | 是 | 创建时间 |
| updated_at | DateTimeField | 是 | 更新时间 |
| is_deleted | BooleanField | 是 | 软删除标记，默认 False |

#### 3.2.2 服务器表 (server)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| hostname | CharField(200) | 是 | 主机名 |
| os | CharField(100) | 否 | 操作系统，如 CentOS 7.9 / Ubuntu 22.04 |
| cpu_cores | IntegerField | 否 | CPU 核数 |
| memory_gb | FloatField | 否 | 内存(GB) |
| disk_gb | FloatField | 否 | 磁盘(GB) |
| cloud_platform | ForeignKey(CloudPlatform) | 否 | 所属云平台 |
| instance_id | CharField(200) | 否 | 云实例 ID |
| ssh_port | IntegerField | 否 | SSH 端口，默认 22 |
| status | CharField(20) | 是 | 状态：running / stopped / terminated / maintenance |
| expire_date | DateField | 否 | 到期时间（包年包月实例） |
| remark | TextField | 否 | 备注 |
| created_at | DateTimeField | 是 | 创建时间 |
| updated_at | DateTimeField | 是 | 更新时间 |
| is_deleted | BooleanField | 是 | 软删除 |

#### 3.2.3 IP 表 (ip_address)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| address | GenericIPAddressField | 是 | IP 地址 |
| ip_type | CharField(20) | 是 | public / private / elastic |
| server | ForeignKey(Server) | 是 | 归属服务器 |
| isp | CharField(50) | 否 | 运营商（电信/联通/移动/BGP） |
| remark | TextField | 否 | 备注 |
| created_at | DateTimeField | 是 | 创建时间 |

**唯一约束**：(address, server) 组合唯一，同一 IP 不可重复归属于同一服务器。

#### 3.2.4 域名表 (domain)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| name | CharField(255) | 是 | 域名，如 example.com，唯一 |
| registrar | ForeignKey(Registrar) | 否 | 注册商 |
| register_date | DateField | 否 | 注册日期 |
| expire_date | DateField | 否 | 到期日期 |
| dns_provider | CharField(100) | 否 | DNS 服务商（DNSPod/CloudFlare 等） |
| icp_status | CharField(20) | 是 | ICP 状态：unfiled / filed / filing / cancelled / exempt |
| remark | TextField | 否 | 备注 |
| created_at | DateTimeField | 是 | 创建时间 |
| updated_at | DateTimeField | 是 | 更新时间 |
| is_deleted | BooleanField | 是 | 软删除 |

#### 3.2.5 端口表 (port)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| number | IntegerField | 是 | 端口号 (1-65535) |
| protocol | CharField(10) | 是 | TCP / UDP |
| service_name | CharField(100) | 否 | 服务名称，如 nginx/mysql/redis/ssh |
| server | ForeignKey(Server) | 是 | 所属服务器 |
| ip | ForeignKey(IP) | 否 | 绑定的具体 IP（为空则监听所有 IP） |
| project | ForeignKey(Project) | 否 | 关联项目 |
| remark | TextField | 否 | 备注 |
| created_at | DateTimeField | 是 | 创建时间 |

**唯一约束**：(number, protocol, server, ip) 组合唯一。

### 3.3 关联中间表设计

#### 3.3.1 项目-服务器关联 (project_server)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| project | ForeignKey(Project) | 是 | 项目 |
| server | ForeignKey(Server) | 是 | 服务器 |
| environment | CharField(20) | 是 | 环境标签：production / staging / testing / development |
| created_at | DateTimeField | 是 | 关联时间 |

**唯一约束**：(project, server) 组合唯一。

#### 3.3.2 域名-IP 关联 (domain_ip)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| domain | ForeignKey(Domain) | 是 | 域名 |
| ip | ForeignKey(IP) | 是 | 目标 IP |
| record_type | CharField(10) | 是 | 记录类型：A / CNAME |
| host_record | CharField(100) | 否 | 主机记录，如 @ / www / api |
| line | CharField(50) | 否 | 解析线路，如默认/移动/联通 |
| ttl | IntegerField | 否 | TTL 值(秒) |
| created_at | DateTimeField | 是 | 创建时间 |

**唯一约束**：(domain, ip, record_type, host_record) 组合唯一。

#### 3.3.3 域名-项目关联 (project_domain)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| project | ForeignKey(Project) | 是 | 项目 |
| domain | ForeignKey(Domain) | 是 | 域名 |
| created_at | DateTimeField | 是 | 关联时间 |

**唯一约束**：(project, domain) 组合唯一。

#### 3.3.4 端口-项目关联 (project_port)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| project | ForeignKey(Project) | 是 | 项目 |
| port | ForeignKey(Port) | 是 | 端口 |
| created_at | DateTimeField | 是 | 关联时间 |

**唯一约束**：(project, port) 组合唯一。

### 3.4 ICP 备案相关表

#### 3.4.1 备案记录表 (icp_record)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| domain | OneToOneField(Domain) | 是 | 关联域名（一对一） |
| icp_number | CharField(100) | 否 | 备案号，如 京ICP备2024XXXXXX号 |
| company_name | CharField(200) | 是 | 主办单位名称 |
| company_type | CharField(20) | 是 | 单位性质：enterprise / individual / government / other |
| contact_person | CharField(50) | 是 | 负责人姓名 |
| contact_phone | CharField(20) | 是 | 负责人联系电话 |
| contact_email | EmailField | 否 | 负责人邮箱 |
| approval_date | DateField | 否 | 审核通过日期 |
| review_remind_date | DateField | 否 | 备案复核提醒日期 |
| status | CharField(20) | 是 | 记录状态：active / changed |
| created_at | DateTimeField | 是 | 创建时间 |
| updated_at | DateTimeField | 是 | 更新时间 |

#### 3.4.2 备案变更历史表 (icp_change_log)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| icp_record | ForeignKey(IcpRecord) | 是 | 关联备案记录 |
| field_name | CharField(50) | 是 | 变更字段名 |
| old_value | TextField | 否 | 变更前值 |
| new_value | TextField | 是 | 变更后值 |
| change_reason | TextField | 否 | 变更原因说明 |
| status | CharField(20) | 是 | 状态：draft / pending / approved / rejected |
| submitted_by | ForeignKey(User) | 是 | 提交人 |
| reviewed_by | ForeignKey(User) | 否 | 审核人 |
| reviewed_at | DateTimeField | 否 | 审核时间 |
| created_at | DateTimeField | 是 | 创建时间 |

### 3.5 云平台相关表

#### 3.5.1 云平台表 (cloud_platform)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| name | CharField(100) | 是 | 平台名称：阿里云/腾讯云/华为云/AWS/Azure/私有化 |
| account_alias | CharField(100) | 否 | 账号别名（便于内部识别） |
| account_id | CharField(200) | 否 | 云平台账号 ID / UIN |
| contact_person | CharField(50) | 否 | 联系人 |
| secret_id | CharField(500) | 否 | API SecretId / AccessKeyId（AES-256 加密存储） |
| secret_key | CharField(1000) | 否 | API SecretKey / AccessKeySecret（AES-256 加密存储） |
| sync_enabled | BooleanField | 是 | 是否启用 API 同步，默认 False |
| sync_regions | JSONField | 否 | 同步地域列表 JSON，如 ["ap-guangzhou","ap-shanghai"] |
| sync_services | JSONField | 否 | 同步服务列表 JSON，如 ["cvm","billing"] |
| sync_interval_minutes | IntegerField | 否 | 自动同步间隔（分钟），默认 360 |
| last_sync_at | DateTimeField | 否 | 最近一次同步完成时间 |
| last_sync_status | CharField(20) | 否 | 最近同步状态：success / failed / partial |
| remark | TextField | 否 | 备注 |
| created_at | DateTimeField | 是 | 创建时间 |
| updated_at | DateTimeField | 是 | 更新时间 |

#### 3.5.2 域名注册商表 (registrar)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| name | CharField(100) | 是 | 注册商名称：腾讯云/阿里云/美橙/易名/GoDaddy 等 |
| account_alias | CharField(100) | 否 | 注册账户别名 |
| account_id | CharField(200) | 否 | 注册账户 ID |
| contact_person | CharField(50) | 否 | 联系人 |
| remark | TextField | 否 | 备注 |
| created_at | DateTimeField | 是 | 创建时间 |

在实际实现中，如果云平台和注册商的管理维度差异较大，建议分成两张表；如果差异较小，可考虑统一为一张 `CloudAccount` 表，通过 `account_type` 区分。本设计采用分表方式以保持灵活性。

### 3.6 云 API 同步相关表

#### 3.6.1 同步日志表 (sync_log)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| cloud_platform | ForeignKey(CloudPlatform) | 是 | 关联云平台账号 |
| sync_type | CharField(20) | 是 | full（全量）/ incremental（增量） |
| trigger | CharField(20) | 是 | manual（手动）/ scheduled（定时） |
| status | CharField(20) | 是 | running / success / failed / partial |
| assets_created | IntegerField | 否 | 本次同步新增资产数 |
| assets_updated | IntegerField | 否 | 本次同步更新资产数 |
| assets_terminated | IntegerField | 否 | 本次标记下线资产数 |
| error_detail | JSONField | 否 | 错误详情 JSON，记录失败的 API 调用及错误信息 |
| started_at | DateTimeField | 是 | 同步开始时间 |
| finished_at | DateTimeField | 否 | 同步结束时间 |

#### 3.6.2 余额记录表 (balance_record)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| cloud_platform | ForeignKey(CloudPlatform) | 是 | 关联云平台账号 |
| cash_balance | DecimalField(12,2) | 否 | 可用现金余额 |
| voucher_balance | DecimalField(12,2) | 否 | 代金券余额 |
| credit_balance | DecimalField(12,2) | 否 | 信用额度 |
| frozen_amount | DecimalField(12,2) | 否 | 冻结金额 |
| total_balance | DecimalField(12,2) | 是 | 总可用余额（现金+代金券） |
| currency | CharField(10) | 是 | 币种：CNY / USD，默认 CNY |
| recorded_at | DateTimeField | 是 | 记录时间（即云平台查询时间） |

**索引**：(cloud_platform, recorded_at) 建立联合索引，支持按时间范围查询余额历史。

### 3.7 告警相关表

#### 3.7.1 告警规则表 (alert_rule)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| name | CharField(200) | 是 | 规则名称 |
| alert_type | CharField(30) | 是 | balance_threshold / resource_expire / sync_failure |
| cloud_platform | ForeignKey(CloudPlatform) | 否 | 告警目标云账号（为空表示所有账号） |
| severity | CharField(20) | 是 | critical（严重）/ warning（警告）/ info（提醒） |
| condition_config | JSONField | 是 | 触发条件 JSON，格式因 alert_type 而异（见下文） |
| cooldown_minutes | IntegerField | 是 | 通知冷却时间（分钟），默认 120 |
| channels | JSONField | 是 | 通知渠道 JSON：["in_app", "email", "wecom"] |
| quiet_start | TimeField | 否 | 免打扰开始时间，如 22:00 |
| quiet_end | TimeField | 否 | 免打扰结束时间，如 08:00 |
| is_enabled | BooleanField | 是 | 是否启用，默认 True |
| created_at | DateTimeField | 是 | 创建时间 |
| updated_at | DateTimeField | 是 | 更新时间 |

**condition_config 格式说明**：

余额阈值告警 `{"type": "balance_threshold", "threshold": 1000, "operator": "lte"}` 表示余额 ≤ 1000 元时告警。
资源到期告警 `{"type": "resource_expire", "days_before": [30, 15, 7], "resource_types": ["server", "domain"]}` 表示到期前 30/15/7 天告警。
同步失败告警 `{"type": "sync_failure", "consecutive_failures": 3}` 表示连续 3 次同步失败时告警。

#### 3.7.2 告警通知人关联表 (alert_rule_users)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| alert_rule | ForeignKey(AlertRule) | 是 | 告警规则 |
| user | ForeignKey(User) | 是 | 通知对象 |
| created_at | DateTimeField | 是 | 创建时间 |

**唯一约束**：(alert_rule, user) 组合唯一。

#### 3.7.3 告警记录表 (alert_record)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| alert_rule | ForeignKey(AlertRule) | 是 | 关联告警规则 |
| alert_type | CharField(30) | 是 | 告警类型（冗余，方便查询） |
| severity | CharField(20) | 是 | critical / warning / info |
| title | CharField(300) | 是 | 告警标题，如「腾讯云账号 xxx 余额不足 100 元」 |
| message | TextField | 是 | 告警详情描述 |
| cloud_platform | ForeignKey(CloudPlatform) | 否 | 关联云账号 |
| related_resource_type | CharField(50) | 否 | 关联资源类型：server / domain / cloud_platform |
| related_resource_id | BigIntegerField | 否 | 关联资源 ID |
| current_value | CharField(200) | 否 | 触发时的实际值，如 "余额: 85.50 元" |
| status | CharField(20) | 是 | triggered（已触发）/ acknowledged（已确认）/ resolved（已解决） |
| acknowledged_by | ForeignKey(User) | 否 | 确认人 |
| acknowledged_at | DateTimeField | 否 | 确认时间 |
| resolved_by | ForeignKey(User) | 否 | 解决人 |
| resolved_at | DateTimeField | 否 | 解决时间 |
| resolve_note | TextField | 否 | 处理备注 |
| triggered_at | DateTimeField | 是 | 触发时间 |
| created_at | DateTimeField | 是 | 创建时间 |

**索引**：(alert_type, status) 联合索引，支持按类型和状态快速筛选；(triggered_at) 索引支持按时间排序。

---

### 3.8 通用审计表

#### 3.8.1 操作日志表 (operation_log)

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | BigAutoField(PK) | 是 | 主键 |
| user | ForeignKey(User) | 是 | 操作人 |
| action | CharField(50) | 是 | 操作类型：create / update / delete / associate / disassociate |
| target_type | CharField(50) | 是 | 目标资源类型：project / server / domain / ip / port / icp_record |
| target_id | BigIntegerField | 是 | 目标资源 ID |
| detail | JSONField | 是 | 变更详情 JSON，存储变更字段的 before/after |
| ip_address | GenericIPAddressField | 否 | 操作来源 IP |
| created_at | DateTimeField | 是 | 操作时间 |

---

## 四、页面交互流程

### 4.1 整体导航结构

```
┌──────────────────────────────────────────────────────┐
│  顶部导航栏                                           │
│  [Logo]  仪表盘  │  资产管理  │  云平台  │  告警  │  拓扑视图  │  系统管理  │ [用户头像] │
└──────────────────────────────────────────────────────┘
┌──────────────┬────────────────────────────────────────┐
│              │                                        │
│  左侧二级菜单 │              主内容区                   │
│              │                                        │
│  ▸ 仪表盘    │                                        │
│  ────────── │                                        │
│  ▸ 项目列表   │                                        │
│  ▸ 服务器列表 │                                        │
│  ▸ 域名列表   │                                        │
│  ▸ IP 列表   │                                        │
│  ▸ 端口列表   │                                        │
│  ────────── │                                        │
│  ▸ ICP 备案  │                                        │
│  ────────── │                                        │
│  ▸ 云平台账号 │                                        │
│  ▸ 域名注册商 │                                        │
│  ▸ 同步日志   │                                        │
│  ────────── │                                        │
│  ▸ 告警规则   │                                        │
│  ▸ 告警记录   │                                        │
│  ────────── │                                        │
│  ▸ 拓扑视图   │                                        │
│  ────────── │                                        │
│  ▸ 用户管理   │                                        │
│  ▸ 角色管理   │                                        │
│  ▸ 操作日志   │                                        │
│              │                                        │
└──────────────┴────────────────────────────────────────┘
```

### 4.2 关键页面交互流程

#### 4.2.1 资产管理列表页通用交互

所有资源列表页遵循统一的交互模式：

```
列表页进入
  │
  ├── 顶部搜索栏：关键字搜索 + 筛选条件（状态下拉/类型筛选等）
  ├── 表格展示：分页列表，每行支持行内操作（编辑/删除）
  ├── 右上角 [新增 XX] 按钮 → 弹出新增表单 Dialog
  ├── 点击行/名称 → 跳转至资源详情页
  └── 支持批量操作（批量删除/导出）
```

#### 4.2.2 资源详情页交互（以服务器详情为例）

```
服务器详情页布局
│
├── 顶部面包屑导航：资产管理 > 服务器 > server-web-01
│
├── 基本信息卡片 (左 60%)
│   ├── 主机名、OS、规格、SSH 端口
│   ├── 云平台：腾讯云 CVM | 实例 ID: ins-xxxx
│   ├── 状态标记 + 到期时间
│   └── [编辑] [删除] 按钮
│
├── 关联资源 Tab 页 (右 40% 或下方)
│   ├── Tab: 关联项目 (2)
│   │   ├── 电商平台-API  [生产]  [解除关联]
│   │   └── [新增关联] 按钮
│   ├── Tab: 网络接口 (3)
│   │   ├── 123.45.67.89 (公网/BGP)
│   │   ├── 10.0.1.10 (内网)
│   │   └── [添加 IP] 按钮
│   ├── Tab: 开放端口 (5)
│   │   ├── 22/TCP (SSH)
│   │   ├── 443/TCP (nginx) → 关联项目: 电商平台-API
│   │   └── [添加端口] 按钮
│   └── Tab: 解析域名 (2)
│       ├── api.example.com → 123.45.67.89 (A记录)
│       └── [查看完整拓扑] 按钮 → 跳转拓扑页面
│
└── 操作日志 Tab: 该服务器的变更记录列表
```

#### 4.2.3 域名详情页交互

```
域名详情页布局
│
├── 基本信息卡片
│   ├── 域名: api.example.com
│   ├── 注册商: 腾讯云 | 注册账户: xxx
│   ├── 注册日期/到期日期
│   └── ICP 状态: 已备案 ──▶ 点击跳转备案信息
│
├── ICP 备案信息卡片
│   ├── 备案号: 京ICP备2024XXXXXX号
│   ├── 主办单位: XX科技有限公司 (企业)
│   ├── 负责人: 张三 | 电话: 138xxxx | 邮箱: xx@xx.com
│   ├── 审核通过日期: 2024-03-15
│   ├── [发起备案变更] 按钮
│   └── [查看变更历史] 按钮 → 展开变更时间线
│
├── DNS 解析记录 Tab
│   ├── 主机记录 @ → 123.45.67.89 (A, 默认线路)
│   ├── 主机记录 www → 123.45.67.89 (A, 默认线路)
│   ├── 主机记录 api → 10.0.1.10 (A, 内网)
│   └── [添加解析记录] 按钮
│
├── 关联项目 Tab
│   ├── 电商平台-API 服务
│   └── [关联项目] 按钮
│
├── 备案变更历史时间线
│   ├── 2026-05-10: 负责人 "张三" → "李四" (已通过)
│   ├── 2025-11-02: 联系电话 "139xxxx" → "138xxxx" (已通过)
│   └── ...
│
└── [查看拓扑] 按钮
```

#### 4.2.4 ICP 备案变更流程交互

```
域名详情页 → [发起备案变更]
  │
  ▼
变更申请表单 (Dialog/页面)
  ├── 变更类型选择：主办单位 / 负责人 / 联系电话 / 邮箱
  ├── 当前值展示（不可编辑，灰色显示）
  ├── 新值输入框
  ├── 变更原因说明（文本框）
  └── [保存草稿] / [提交审核]
        │
        ▼
  审核列表页 (需要审核权限)
  ├── 待审核列表
  ├── 查看变更对比 (Before/After)
  └── [通过] / [驳回（需填写驳回原因）]
        │
        ▼
  审核通过后：
  ├── 自动更新 icp_record 表对应字段
  ├── 在 icp_change_log 表记录变更历史
  └── 通知提交人（站内消息）
```

#### 4.2.5 拓扑视图页交互

```
┌─────────────────────────────────────────────────────────┐
│  搜索框: [输入资源名称/IP/域名搜索...]  [项目筛选: 全部 ▼] │
│  [显示/隐藏] ☑项目 ☑服务器 ☑IP ☑域名 ☑端口  [全屏] [导出] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                                                         │
│               ┌────────┐                                │
│           ┌───│ 项目A  │───┐                            │
│           │   └────────┘   │                            │
│           ▼                ▼                            │
│      ┌─────────┐     ┌─────────┐                       │
│      │服务器-A  │     │服务器-B  │                       │
│      └────┬────┘     └────┬────┘                       │
│           │               │                            │
│           ▼               ▼                            │
│      ┌────────┐      ┌────────┐                       │
│      │IP-公网 │      │IP-内网 │                        │
│      └───┬────┘      └────────┘                       │
│          │                                             │
│          ▼                                             │
│      ┌────────┐     ┌─────────────────┐                │
│      │ 域名A  │────▶│ 侧边栏详情卡片   │                │
│      └────────┘     │                 │                │
│                     │ 域名: xxx.com   │                │
│                     │ 状态: 已备案    │                │
│                     │ 注册商: 腾讯云  │                │
│                     │ ────────────── │                │
│                     │ 解析IP:        │                │
│                     │ · 123.45.67.89 │                │
│                     │ ────────────── │                │
│                     │ 关联项目:      │                │
│                     │ · 项目A        │                │
│                     │ ────────────── │                │
│                     │ 部署服务器:    │                │
│                     │ · 服务器-A     │                │
│                     │ ────────────── │                │
│                     │ [查看完整详情] │                │
│                     └─────────────────┘                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 4.2.6 仪表盘页面

系统入口仪表盘，提供全局概览：

```
┌──────────────────────────────────────────────────────┐
│  仪表盘                                              │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ 项目总数  │ 服务器总数│ 域名总数  │ IP 总数   │ 端口总数 │
│   12     │   45     │   23     │   89     │  156    │
├──────────┴──────────┴──────────┴──────────┴─────────┤
│                                                      │
│  ┌─────────────────────┐  ┌──────────────────────┐  │
│  │ 即将到期资源          │  │ ICP 备案状态分布      │  │
│  │ · server-03 7天后   │  │ 已备案: 18   80%     │  │
│  │ · xxx.com 15天后    │  │ 备案中: 2    10%     │  │
│  │ · ...               │  │ 未备案: 1    5%      │  │
│  └─────────────────────┘  │ 无需备案: 2   5%     │  │
│                            └──────────────────────┘  │
│  ┌──────────────────────────────────────────────┐    │
│  │  最近操作日志                                  │    │
│  │  2026-06-29 14:30  张三 编辑了服务器 server-01 │    │
│  │  2026-06-29 11:20  李四 新增了域名 xxx.com     │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

#### 4.2.7 云平台账号详情页交互

```
云平台账号详情页布局
│
├── 顶部面包屑导航：云平台 > 腾讯云-生产账号
│
├── 基本信息卡片
│   ├── 平台名称: 腾讯云 | 账号别名: 生产账号
│   ├── 账号 ID: 100012345678
│   ├── 联系人: 张三
│   ├── API 状态: ● 已连接（上次同步: 2026-06-29 12:00，成功）
│   └── [编辑] [测试连接] [立即同步] 按钮
│
├── API 凭证卡片
│   ├── SecretId: AKID****abcd（脱敏展示）
│   ├── [重新配置凭证] 按钮
│   └── [测试连接] 按钮 → 弹窗显示测试结果
│
├── 同步配置卡片
│   ├── 同步地域: ☑ 广州 ☑ 上海 ☐ 北京 ☐ 成都
│   ├── 同步服务: ☑ CVM 云服务器 ☑ 账户余额
│   ├── 同步周期: 每 [6] 小时自动同步
│   └── [保存配置]
│
├── Tab: 关联资源
│   ├── 服务器列表 (12 台) — 展示实例 ID/名称/状态/到期时间
│   └── [查看拓扑] 按钮
│
├── Tab: 余额历史
│   ├── 当前余额: ¥ 8,520.30（现金 ¥7,200 + 代金券 ¥1,320.30）
│   ├── 余额趋势折线图（近 90 天）
│   ├── 余额记录列表（分页）
│   └── [手动查询余额] 按钮
│
└── Tab: 同步日志
    ├── 同步记录列表：时间 / 类型 / 状态 / 新增/更新/下线数量
    ├── 点击某条记录 → 展开同步详情（错误信息等）
    └── [手动触发同步] 按钮
```

#### 4.2.8 告警中心交互

**告警规则管理页**：

```
告警规则列表页
│
├── 顶部操作栏：[新增规则] 按钮 + 筛选（类型/状态/级别）
│
├── 规则列表表格
│   ├── 规则名称          | 类型      | 级别 | 状态 | 上次触发      | 操作
│   ├── 腾讯云余额不足告警 | 余额阈值   | 严重 | 启用 | 2026-06-29   | [编辑][停用][删除]
│   ├── CVM到期提醒       | 资源到期   | 警告 | 启用 | —           | [编辑][停用][删除]
│   └── 同步失败告警      | 同步失败   | 严重 | 启用 | 2026-06-28   | [编辑][停用][删除]
│
└── 新增/编辑规则 Dialog
    ├── 规则名称
    ├── 告警类型下拉：余额阈值 / 资源到期 / 同步失败
    ├── 告警目标：全部云账号 / 指定云账号（下拉选择）
    ├── 触发条件（按类型动态切换）：
    │   · 余额阈值：当余额 ≤ [1000] 元 时触发
    │   · 资源到期：到期前 [30, 15, 7] 天触发（可添加多级阈值）
    │   · 同步失败：连续 [3] 次同步失败时触发
    ├── 告警级别：严重 / 警告 / 提醒
    ├── 通知渠道：☑ 站内消息 ☑ 邮件 ☐ 企业微信
    ├── 通知对象：选择用户（多选）
    ├── 冷却时间：[120] 分钟
    ├── 免打扰时段：☐ 启用  开始 [22:00]  结束 [08:00]
    └── [保存] [取消]
```

**告警记录页**：

```
告警记录列表页
│
├── 筛选栏：级别（全部/严重/警告/提醒）、状态（全部/已触发/已确认/已解决）、时间范围
│
├── 统计卡片：今日告警数 | 未处理数 | 已确认数 | 已解决数
│
├── 告警记录列表
│   ├── ● 严重 | 腾讯云账号 生产账号 余额不足 100 元 | 余额: ¥85.50 | 2026-06-29 10:00
│   │     [确认] [解决] [查看详情]
│   ├── ● 警告 | 服务器 server-db-01 将于 7 天后到期 | 到期日: 2026-07-06 | 2026-06-29 09:00
│   │     [确认] [解决] [查看详情]
│   └── ● 提醒 | api.example.com 域名将于 15 天后到期 | 到期日: 2026-07-14 | 2026-06-29 08:00
│         [确认] [解决] [查看详情]
│
└── 点击"查看详情" → 弹窗或跳转详情页
     ├── 告警标题、级别、触发时间
     ├── 触发条件描述：规则「腾讯云余额不足告警」: 余额 ≤ 1000 元
     ├── 当前值: 余额 ¥85.50
     ├── 关联资源链接（点击跳转云账号详情页）
     ├── 处理状态时间线：触发 → 确认（张三, 10:15）→ 解决（张三, 10:30，"已充值"）
     └── [确认告警] / [标记解决] 按钮
```

---

## 五、关键业务逻辑

### 5.1 资源关联追溯算法

系统需要支持从任意资源节点出发，追溯其上下游关联链路。以下为各资源的追溯逻辑：

**从项目出发（下游追溯）**：
```
输入: 项目 ID
步骤:
  1. 查询 project_server 表 → 获取关联的服务器列表
  2. 对每台服务器：
     a. 查询 ip_address 表 (WHERE server_id = X) → 获取 IP 列表
     b. 查询 port 表 (WHERE server_id = X) → 获取端口列表
  3. 对每个 IP：
     a. 查询 domain_ip 表 (WHERE ip_id = X) → 获取域名列表
  4. 查询 project_domain 表 (WHERE project_id = 项目ID) → 获取直接关联的域名
  5. 汇总去重，构建链路树
```

**从域名出发（上游追溯）**：
```
输入: 域名 ID
步骤:
  1. 查询 domain_ip 表 → 获取解析目标 IP 列表
  2. 对每个 IP：查询 ip_address 表 → 获取归属服务器
  3. 对每台服务器：
     a. 查询 project_server 表 → 获取部署的项目列表
     b. 查询 port 表 → 获取开放端口列表
  4. 查询 project_domain 表 → 获取直接关联的项目列表
  5. 查询 icp_record 表 → 获取备案信息
  6. 汇总去重，构建链路树
```

**从 IP 出发（双向追溯）**：
```
输入: IP ID
步骤:
  向上追溯 (上游)：
    1. 查询 ip_address 表 → 获取归属服务器
    2. 查询 project_server 表 → 获取部署的项目
    3. 对每个项目，查询 project_domain → 获取关联域名
  向下追溯 (下游)：
    1. 查询 domain_ip 表 → 获取解析至该 IP 的域名
    2. 查询 port 表 (WHERE ip_id = X) → 获取绑定在该 IP 上的端口
  汇总去重，构建双向链路
```

### 5.2 影响分析算法

当某资源状态发生变更（如服务器下线）时，系统需自动评估影响范围：

```
输入: 资源类型 & 资源 ID & 变更类型(下线/维护/删除)
步骤:
  1. 调用 5.1 中的追溯算法，获取该资源的完整上下游链路
  2. 按资源类型分类统计影响范围：
     - 影响的项目列表
     - 影响的域名列表
     - 影响的 IP 列表
     - 影响的端口列表
  3. 对影响范围内的每个资源，检查是否有冗余/备用方案：
     - 域名是否还有其他解析 IP？
     - 项目是否还部署在其他服务器上？
  4. 生成影响分析报告，标注高/中/低风险等级
输出: 影响分析报告 JSON
```

**风险等级定义**：
- **高风险**：资源下线后，有项目/域名完全没有备用方案，直接不可用
- **中风险**：资源下线后，有项目/域名的部分功能受影响，但有备用
- **低风险**：资源下线后，影响范围内的资源均有完整冗余

### 5.3 ICP 备案变更流程

```
变更流程状态机：
                ┌─────────┐
                │  draft  │ (草稿)
                └────┬────┘
                     │ 提交审核
                     ▼
                ┌─────────┐
         ┌──────│ pending │ (待审核)
         │      └────┬────┘
         │           │
         │    ┌──────┼──────┐
         │    ▼             ▼
         │ ┌──────────┐ ┌──────────┐
         │ │ rejected │ │ approved │ (通过)
         │ │ (驳回)    │ └────┬─────┘
         │ └────┬─────┘      │
         │      │            │ 自动更新 icp_record
         │      │ 重新提交    │ 记录变更历史
         │      ▼            │
         │ ┌─────────┐       │
         └─│ pending │◄──────┘ (可重新提交)
           └─────────┘
```

**审核规则**：
- 变更申请提交后，需由具有 `icp_review` 权限的用户审核
- 审核通过后系统自动更新 `icp_record` 对应字段，无需手动操作
- 审核驳回时需填写驳回原因，支持驳回后修改重新提交
- 同一域名的同一字段如果存在 `pending` 状态的变更，不允许再次提交该字段的变更

### 5.4 到期提醒逻辑

系统定时任务（每日执行）扫描以下资源的到期时间：

| 资源 | 检查字段 | 提醒阈值 |
|---|---|---|
| 服务器 | expire_date | 30天 / 15天 / 7天 |
| 域名 | expire_date | 30天 / 15天 / 7天 |
| ICP 备案 | review_remind_date | 30天 / 15天 |

提醒方式：
- 仪表盘"即将到期"卡片中展示
- 站内通知
- 可对接企业微信/邮件通知（通过 Django signal 或 Celery 定时任务）

### 5.5 云平台 API 同步逻辑

#### 5.5.1 同步调度策略

系统通过 Celery Beat 实现定时同步调度，同时支持手动触发：

```
Celery Beat 定时调度
  │
  ├── 每分钟扫描 cloud_platform 表
  │     获取所有 sync_enabled=True 的账号
  │
  ├── 对每个账号：
  │     │ last_sync_at + sync_interval_minutes ≤ now ?
  │     │
  │     ├── 是 → 创建 sync_task 异步任务
  │     │
  │     └── 否 → 跳过
  │
  └── 手动触发：直接创建 sync_task，不受间隔限制
```

#### 5.5.2 资产同步流程（以腾讯云 CVM 为例）

```
输入: cloud_platform_id
步骤:
  1. 从 cloud_platform 表获取 API 凭证（SecretId/SecretKey）和 sync_regions
  2. 创建 sync_log 记录，状态为 running
  3. 对每个 sync_region：
     a. 调用 tencentcloud-sdk-python 的 DescribeInstances API
     b. 获取该地域所有 CVM 实例列表
     c. 对每个实例进行字段映射：
        - InstanceId → instance_id
        - InstanceName → hostname
        - OsName → os
        - CPU → cpu_cores
        - Memory → memory_gb
        - SystemDisk.DiskSize → disk_gb
        - PublicIpAddresses → 创建或更新 IP 记录（ip_type=public）
        - PrivateIpAddresses → 创建或更新 IP 记录（ip_type=private）
        - InstanceState → status 映射（RUNNING→running, STOPPED→stopped, TERMINATED→terminated）
        - ExpiredTime → expire_date
        - Placement.Zone → 存入 extra_data JSON
     d. 与本地 Server 表做 Diff（按 instance_id 匹配）
  4. 差异处理：
     - 新增实例（云端有、本地无）→ 创建 Server + IP 记录
     - 更新实例（云端有、本地有且属性变化）→ 更新 Server + 同步 IP
     - 已销毁实例（云端已不存在、本地状态非 terminated）→ 标记 status=terminated
  5. 如果 sync_services 包含 "billing"，执行余额同步（见 5.5.3）
  6. 更新 sync_log 状态为 success/failed/partial
  7. 更新 cloud_platform.last_sync_at 和 last_sync_status
输出: sync_log 记录
```

#### 5.5.3 余额同步流程

```
输入: cloud_platform_id
步骤:
  1. 从 cloud_platform 表获取 API 凭证
  2. 调用云平台 Billing/Account API 查询余额
     - 腾讯云：调用 DescribeAccountBalance API
     - 阿里云：调用 QueryAccountBalance API
  3. 解析返回结果：
     - 现金余额 (CashBalance)
     - 代金券余额 (VoucherBalance)
     - 信用额度 (CreditBalance)
     - 冻结金额 (FrozenAmount)
  4. 计算总余额 = 现金余额 + 代金券余额
  5. 写入 balance_record 表
  6. 触发余额告警评估（见 5.6）
输出: balance_record 记录
```

#### 5.5.4 适配器模式设计

由于不同云平台的 API 接口差异较大，系统采用**适配器模式**实现多云平台统一调用：

```
                    ┌──────────────────┐
                    │  SyncService     │ (同步编排服务)
                    │  - sync_assets() │
                    │  - sync_balance()│
                    └────────┬─────────┘
                             │ 依赖
                             ▼
                    ┌──────────────────┐
                    │ CloudAdapter     │ (抽象适配器接口)
                    │ (ABC 抽象基类)   │
                    │ + list_instances │
                    │ + get_balance    │
                    │ + test_connect   │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │TencentAdapter│  │ AliyunAdapter│  │HuaweiAdapter │
  │ (腾讯云SDK)   │  │ (阿里云SDK)   │  │ (华为云SDK)   │
  └──────────────┘  └──────────────┘  └──────────────┘

扩展新平台只需实现 CloudAdapter 接口即可，无需修改 SyncService 逻辑。
```

### 5.6 告警评估与通知逻辑

#### 5.6.1 告警评估流程

告警评估在以下时机触发：
- 余额同步完成后
- 每日定时任务（到期扫描）
- 同步任务完成后（失败检测）

```
告警评估引擎流程:
  1. 获取所有 is_enabled=True 的 alert_rule
  2. 按 alert_type 分类评估：

     【余额阈值告警】
     - 获取云账号最近一条 balance_record
     - 若 total_balance ≤ condition_config.threshold → 触发告警
     - 检查冷却期：若该规则在 cooldown_minutes 内已触发过 → 跳过

     【资源到期告警】
     - 扫描 server 表 WHERE expire_date - NOW() IN condition_config.days_before
     - 扫描 domain 表 WHERE expire_date - NOW() IN condition_config.days_before
     - 每条到期资源生成一条告警记录
     - 同一条规则+同一资源在冷却期内不重复触发

     【同步失败告警】
     - 查询 sync_log 表，统计该云账号最近 N 条的 status
     - 若连续 failure 次数 ≥ condition_config.consecutive_failures → 触发告警
     - 同步恢复成功后自动标记该类告警为 resolved

  3. 创建 alert_record，状态为 triggered
  4. 调用通知分发（见 5.6.2）
```

#### 5.6.2 通知分发逻辑

```
通知分发流程:
  1. 获取告警规则的 channels 配置和 notify_users 列表
  2. 检查当前时间是否在 quiet_start ~ quiet_end 免打扰时段内：
     - 是 → 仅写站内消息，邮件/企业微信延迟至 quiet_end 后发送
     - 否 → 立即按 channels 配置发送
  3. 各渠道通知方式：
     - 站内消息：写入 Django 内置通知表，前端轮询或 WebSocket 推送
     - 邮件：通过 Django send_mail + SMTP 发送格式化 HTML 邮件
     - 企业微信：调用 Webhook 推送 Markdown 格式消息卡片
  4. 记录通知发送日志（成功/失败），失败时重试 1 次
```

#### 5.6.3 告警收敛策略

| 收敛策略 | 说明 |
|---|---|
| 冷却期 | 同一规则在 cooldown_minutes 内不重复触发通知 |
| 资源去重 | 同一资源+同一规则在冷却期内仅产生一条告警记录 |
| 自动恢复 | 同步失败告警在下次同步成功后自动标记为 resolved |
| 日汇总 | 可选：每日 09:00 发送告警汇总报告（"今日共触发 3 条告警，1 条未处理"）|

#### 5.6.4 仪表盘告警卡片集成

新增仪表盘告警概览卡片：

```
┌─────────────────────────────────────────────┐
│  ⚠️ 告警概览                                  │
│                                             │
│  🔴 严重: 2   🟡 警告: 3   🔵 提醒: 5       │
│                                             │
│  最新告警:                                    │
│  ● 严重  腾讯云 余额不足 100 元  10 分钟前     │
│  ● 严重  阿里云 连续 3 次同步失败  1 小时前    │
│  ● 警告  server-db-01 7天后到期  2 小时前     │
│                                             │
│  [查看全部告警 →]                             │
└─────────────────────────────────────────────┘
```

### 5.5 数据一致性保障

| 场景 | 处理策略 |
|---|---|
| 删除服务器 | 级联标记关联的 IP、端口为"已失效"状态，保留历史关联记录 |
| 删除 IP | 自动解除 domain_ip 中的关联记录，记录操作日志 |
| 删除项目 | 解除与服务器、域名的关联，端口标记为"未关联项目" |
| 域名备案状态变更 | 如果域名从"已备案"变更为"备案注销"，对应的 icp_record 标记为 `cancelled` |

**软删除策略**：所有核心实体均采用软删除（`is_deleted=True`），数据不物理删除，确保关联关系可追溯。前端列表页默认过滤 `is_deleted=True` 的记录，管理员可在筛选条件中选择"显示已删除"。

---

## 六、非功能性需求

### 6.1 性能要求

| 指标 | 要求 |
|---|---|
| 页面加载时间 | 列表页 < 2s，详情页 < 1.5s |
| 拓扑图渲染 | 节点数 < 500 时，渲染时间 < 3s |
| API 响应时间 | P99 < 500ms |
| 并发用户数 | 支持 50+ 并发用户 |

### 6.2 安全要求

- 所有 API 接口需进行权限校验
- 敏感操作（删除、备案变更审核）需二次确认
- 操作日志不可删除
- 云平台 API 密钥（SecretId/SecretKey）采用 AES-256-CBC 加密存储于数据库，密钥加密密钥（KEK）由环境变量注入，不写入配置文件或代码仓库
- 密钥展示时强制脱敏，仅显示前 4 位 + 后 4 位（如 `AKID****xyz`）
- 支持登录失败锁定（5次失败锁定 30 分钟）
- 邮件/企业微信通知中不展示敏感信息

### 6.3 可扩展性

- 数据模型预留扩展字段（JSONField）以适应未来新增属性
- 拓扑图支持自定义节点样式和布局算法切换
- 备案变更审核流程支持自定义审批链（未来可扩展）
- 云平台适配器采用策略模式，新增云平台只需新增 Adapter 实现类，无需改动核心同步逻辑
- 告警通知渠道采用插件化设计，新增渠道（如钉钉、飞书）只需实现 `Notifier` 接口

### 6.4 云 API 专项要求

| 指标 | 要求 |
|---|---|
| SDK 依赖管理 | 各云平台 SDK 作为可选依赖，仅安装所需平台的 SDK |
| API 限流保护 | 遵守云平台 API 调用频率限制，内置请求间隔控制（默认 500ms/次） |
| 凭证失效处理 | 同步时若返回鉴权失败（AuthFailure），自动标记 sync_enabled=False 并触发告警 |
| 同步超时 | 单地域同步超时 5 分钟，单账号总体同步超时 30 分钟 |
| 数据一致性 | 同步过程中若发生异常，已同步的数据不回滚，仅标记 sync_log.status=partial |

---

## 七、项目工程结构

基于前后端分离架构，项目拆分为两个独立的代码仓库（或 Monorepo 下的两个顶级目录）：

```
cloudweave/                         # 项目根（Monorepo）
├── backend/                        # Django 后端
│   ├── apps/
│   │   ├── accounts/               # 用户 & 认证 & 权限（含 JWT 配置）
│   │   ├── assets/                 # 核心资产管理（Project, Server, IP, Domain, Port）
│   │   ├── relations/              # 关联关系管理（中间表逻辑 & 追溯算法）
│   │   ├── icp/                    # ICP 备案管理
│   │   ├── cloud/                  # 云平台账号 & 注册商管理（模型 + 凭证管理）
│   │   ├── sync/                   # 云 API 集成
│   │   │   ├── adapters/           # 各平台适配器实现
│   │   │   ├── tasks.py            # Celery 定时 & 异步任务
│   │   │   └── services.py         # 同步编排服务
│   │   ├── alerts/                 # 告警引擎
│   │   │   ├── engine.py           # 告警评估引擎
│   │   │   ├── notifiers/          # 通知渠道实现
│   │   │   └── tasks.py            # 定时扫描 Celery 任务
│   │   ├── topology/               # 拓扑数据 API
│   │   └── audit/                  # 操作日志 & 审计
│   ├── cloudweave/                 # Django 项目配置目录
│   │   ├── settings/
│   │   │   ├── base.py             # 基础配置
│   │   │   ├── dev.py              # 开发环境
│   │   │   └── prod.py             # 生产环境
│   │   ├── urls.py                 # 根路由（/api/v1/...）
│   │   ├── celery.py               # Celery 配置
│   │   └── asgi.py                 # ASGI 配置（WebSocket）
│   ├── requirements.txt
│   ├── Dockerfile
│   └── manage.py
│
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── api/                    # API 请求层（按模块拆分）
│   │   │   ├── assets.ts           # 资产管理 API
│   │   │   ├── cloud.ts            # 云平台 API
│   │   │   ├── sync.ts             # 同步管理 API
│   │   │   ├── alerts.ts           # 告警 API
│   │   │   ├── topology.ts         # 拓扑 API
│   │   │   ├── icp.ts              # ICP 备案 API
│   │   │   └── auth.ts             # 认证 API（登录/刷新 Token）
│   │   ├── views/                  # 页面组件（按功能模块）
│   │   │   ├── dashboard/          # 仪表盘
│   │   │   ├── assets/             # 资产管理（项目/服务器/域名/IP/端口）
│   │   │   ├── cloud/              # 云平台账号 & 余额
│   │   │   ├── alerts/             # 告警规则 & 告警记录
│   │   │   ├── topology/           # 可视化拓扑
│   │   │   ├── icp/                # ICP 备案管理
│   │   │   └── system/             # 系统管理（用户/角色/日志）
│   │   ├── components/             # 通用业务组件
│   │   │   ├── common/             # 通用 UI 组件（搜索栏、分页器等）
│   │   │   ├── assets/             # 资产管理组件（服务器卡片、域名列表等）
│   │   │   └── topology/           # 拓扑组件（节点、连线、侧边栏）
│   │   ├── composables/            # Vue 组合式函数（通用逻辑复用）
│   │   ├── router/                 # 路由配置
│   │   ├── stores/                 # Pinia 状态管理
│   │   ├── utils/                  # 工具函数
│   │   └── types/                  # TypeScript 类型定义
│   ├── public/
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── Dockerfile
│   └── index.html
│
├── docker-compose.yml              # 本地开发一键启动
│   # services: postgres, redis, backend, frontend, nginx
├── nginx/
│   └── default.conf                # Nginx 反向代理配置
└── README.md
```

### 后端 API 设计规范

| 规范项 | 说明 |
|---|---|
| URL 风格 | RESTful，资源复数命名：`/api/v1/servers/`、`/api/v1/projects/` |
| HTTP 方法 | GET（查询）、POST（创建）、PUT/PATCH（更新）、DELETE（删除） |
| 响应格式 | 统一 JSON 结构：`{"code": 0, "data": {...}, "message": "ok"}` |
| 分页 | 统一使用 `page` + `page_size` 参数，响应包含 `total`、`page`、`page_size` |
| 错误码 | 统一业务错误码枚举，前端按 code 做统一处理（如 401 = Token过期，自动刷新） |
| 权限 | ViewSet 级别 permission_classes + 数据级权限过滤（按项目/团队隔离） |
| 过滤 | django-filter 集成，支持 `?status=running&cloud_platform=1` 链式过滤 |
| 排序 | `?ordering=-created_at` 按创建时间倒序 |
| API 文档 | `/api/docs/` Swagger UI，开发环境自动开启 |

### 前端路由设计

| 路由 | 页面 | 权限 |
|---|---|---|
| `/login` | 登录页 | 公开 |
| `/` | 仪表盘 | 登录用户 |
| `/assets/projects` | 项目列表 | 登录用户 |
| `/assets/projects/:id` | 项目详情 | 登录用户 |
| `/assets/servers` | 服务器列表 | 登录用户 |
| `/assets/servers/:id` | 服务器详情 | 登录用户 |
| `/assets/domains` | 域名列表 | 登录用户 |
| `/assets/domains/:id` | 域名详情 | 登录用户 |
| `/assets/ips` | IP 列表 | 登录用户 |
| `/assets/ports` | 端口列表 | 登录用户 |
| `/cloud/accounts` | 云平台账号列表 | 登录用户 |
| `/cloud/accounts/:id` | 云账号详情（含余额/同步配置） | 登录用户 |
| `/cloud/registrars` | 域名注册商列表 | 登录用户 |
| `/cloud/sync-logs` | 同步日志 | 登录用户 |
| `/icp` | ICP 备案列表 | 登录用户 |
| `/alerts/rules` | 告警规则管理 | 管理员 |
| `/alerts/records` | 告警记录中心 | 登录用户 |
| `/topology` | 可视化拓扑图 | 登录用户 |
| `/system/users` | 用户管理 | 管理员 |
| `/system/roles` | 角色管理 | 管理员 |
| `/system/logs` | 操作日志 | 管理员 |
| `/403` | 无权限提示页 | 公开 |
| `/:pathMatch(.*)*` | 404 | 公开 |

---

## 八、里程碑规划建议

| 阶段 | 内容 | 产出 |
|---|---|---|
| Phase 1 (MVP) | 资产管理模块（项目/服务器/域名/IP/端口的 CRUD）+ 基本关联配置 + 云平台账号管理（含 API 凭证） | 可用的资源登记与管理平台 |
| Phase 2 | 关联关系追溯算法 + 影响分析 + 操作日志 + 云平台 API 适配器框架 | 完整的关联追踪能力 + 多云适配器基础 |
| Phase 3 | ICP 备案管理（备案登记 + 变更流程 + 变更历史）+ 服务器资产同步（腾讯云） | 合规管理能力 + 单平台自动同步 |
| Phase 4 | 可视化拓扑图 + 交互探索 + 多平台资产同步（阿里云/华为云） | 图形化运维视图 + 多云同步覆盖 |
| Phase 5 | 余额同步 + 告警规则引擎 + 告警通知（站内/邮件/企业微信） + 仪表盘增强 | 自动化告警闭环 + 运维成本可观测 |
| Phase 6 | 高级告警（收敛/日汇总）+ 免打扰 + 移动端适配 + 数据导出报表 | 企业级运维体验 |

---

## 附录 A：术语表

| 术语 | 说明 |
|---|---|
| 资源节点 (Resource Node) | 拓扑图中的基本单元，代表一个项目/服务器/域名/IP/端口实体 |
| 关联链路 (Association Chain) | 从某一节点出发，沿关联关系追溯到的完整上下游节点序列 |
| 一度关联 | 与当前节点直接相连的节点 |
| 上游追溯 | 从域名/IP 向部署服务器和项目的方向追溯 |
| 下游追溯 | 从项目向服务器、IP、域名、端口的方向追溯 |
| 影响分析 (Impact Analysis) | 评估某资源状态变更对其他资源产生的影响范围 |
| 软删除 (Soft Delete) | 标记数据为已删除但不物理清除，保留数据可追溯性 |
| ICP 备案 | 互联网信息服务备案（Internet Content Provider filing），中国境内网站必须完成的合规手续 |

---

> 本 PRD 为运维管理系统 v1.0 需求文档，后续按阶段迭代实施。如有需求变更，请同步更新本文档版本号与变更记录。
