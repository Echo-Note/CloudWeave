# API 权限自动扫描与批量生成功能设计

**日期：** 2026-04-09
**状态：** 设计完成，等待评审

---

## 1. 概述

### 背景
当前后端接口权限很多，前端给角色分配权限时需要手动一个个添加按钮权限，操作繁琐。系统需要提供自动化能力，自动扫描 Django app 下的 ViewSet 接口，并批量生成 `MenuButton` 权限记录。

### 目标
在**菜单管理页面**，管理员选中一个菜单后，点击"自动扫描"按钮，选择目标 Django app，系统自动扫描该 app 下所有 ViewSet 的接口，预览生成的按钮权限列表（支持分组展示和行内编辑），确认后批量创建 `MenuButton` 记录并关联到当前菜单。

---

## 2. 功能流程

```
[菜单管理页面]
       │
       ▼
管理员选中一个菜单
       │
       ▼
点击「自动扫描」按钮
       │
       ▼
弹出扫描配置弹窗
  ├── 选择目标 Django app（下拉框，列出所有 app）
  └── 点击「开始扫描」
       │
       ▼
后端 API：扫描 app 下所有 ViewSet → 返回检测到的接口列表
       │
       ▼
前端展示「扫描结果预览」分组表格
  ├── 按 ViewSet 分组，可折叠
  ├── 列：勾选 | ViewSet名 | 接口路径 | HTTP方法 | 按钮名称(name) | 权限标识(value)
  ├── 自动根据 docstring 生成 name，否则用固定规则
  ├── 自动生成 value（app:ViewSet:Action 格式）
  └── 支持行内编辑 name 和 value
       │
       ▼
管理员勾选需要生成的接口，编辑名称/value
       │
       ▼
点击「确认生成」
       │
       ▼
后端 API：批量创建 MenuButton 记录
  ├── api 字段：完整接口路径
  ├── menu 字段：关联到当前选中的菜单
  ├── name / value：使用前端提交的名称
  └── method：根据 HTTP 方法映射
       │
       ▼
刷新当前菜单的按钮列表，显示新增的权限
```

---

## 3. 后端设计

### 3.1 新增 API

#### API 1：获取可扫描的 Django App 列表

- **URL：** `GET /api/system/menu_button/scan_get_apps/`
- **功能：** 扫描 Django INSTALLED_APPS 下所有自定义 app，返回 app 名称列表
- **响应：** `["system", "blog", "api"]`
- **权限：** 超级管理员

#### API 2：扫描 App 下的接口并返回预览数据

- **URL：** `POST /api/system/menu_button/scan_viewset/`
- **请求体：** `{ "app": "system" }`
- **功能：** 扫描指定 app 下所有 ViewSet，自动路由，推断每个 action 的信息
- **响应：**

```json
{
  "data": [
    {
      "viewset": "MenuViewSet",
      "viewset_verbose_name": "菜单管理",
      "buttons": [
        {
          "path": "/api/system/menu/",
          "method": "GET",
          "action": "list",
          "name": "列表查询",
          "value": "system:Menu:List",
          "is_existing": false
        },
        {
          "path": "/api/system/menu/",
          "method": "POST",
          "action": "create",
          "name": "新增菜单",
          "value": "system:Menu:Create",
          "is_existing": true
        }
      ]
    }
  ]
}
```

- **字段说明：**
  - `name`：优先使用 ViewSet action 的 docstring，否则按固定规则生成
  - `value`：格式 `{app}:{ViewSet}:{Action}`，首字母大写
  - `is_existing`：该 value 是否已存在于数据库（避免重复创建）
- **权限：** 超级管理员

#### API 3：批量创建 MenuButton

- **URL：** `POST /api/system/menu_button/scan_batch_create/`
- **请求体：**

```json
{
  "menu_id": 12,
  "buttons": [
    {
      "path": "/api/system/menu/",
      "method": "GET",
      "action": "list",
      "name": "列表查询",
      "value": "system:Menu:List"
    },
    {
      "path": "/api/system/menu/",
      "method": "POST",
      "action": "create",
      "name": "新增菜单",
      "value": "system:Menu:Create"
    }
  ]
}
```

- **功能：** 批量创建 MenuButton，跳过已存在的记录（按 value 去重）
- **响应：** `{ "count": 5, "skipped": 2 }`
- **权限：** 超级管理员

### 3.2 ViewSet 扫描算法

```
输入：app_name（字符串，如 "system"）
输出：List[Dict]（每个 ViewSet 及其 action 信息）

1. 导入 app 下的 models.py（如果有），提取 model 名称用于翻译
2. 获取 app 下所有继承自 GenericViewSet / ModelViewSet 的类
3. 对每个 ViewSet：
   a. 提取类名（如 MenuViewSet → Menu）
   b. 获取该 ViewSet 注册的所有路由（action 方法 + 标准 CRUD）
   c. 对每个 action：
      - 获取 HTTP 方法（getattr(viewset, action).mapping.keys()）
      - 获取 docstring 作为 name 候选
      - 生成 value：{app}:{ModelName}:{ActionName}
      - 查询 MenuButton 表，检查 value 是否已存在
4. 合并结果，按 ViewSet 分组返回
```

### 3.3 数据模型（无需新增）

复用现有 `MenuButton` 模型，无需修改。

---

## 4. 前端设计

### 4.1 菜单位置

在**菜单管理页面**（`/web/src/views/system/menu/`）的工具栏区域，增加"自动扫描"按钮。

### 4.2 扫描配置弹窗

- **触发：** 点击"自动扫描"按钮（需先选中一个菜单行）
- **未选中菜单：** 提示"请先选择一个菜单"
- **弹窗内容：**
  - 标题："自动扫描接口权限"
  - 表单：目标 App 下拉框（从 API 加载 app 列表）
  - 按钮：「开始扫描」

### 4.3 扫描结果预览弹窗（Modal）

- **大小：** 宽度 90%，最大 1200px
- **布局：** 分组表格

```
┌─ 扫描结果预览 ─────────────────────────────────────────────┐
│  目标App: system                              已选择: 12项 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 全选   ViewSet名    接口路径      方法  按钮名称    value│ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ▶ MenuViewSet (菜单管理)                               ▼│ │
│ │  ☑   /api/system/menu/   GET    列表查询   system:Menu:List│ │
│ │  ☑   /api/system/menu/   POST   新增菜单   system:Menu:Create│ │
│ │  ☑   /api/system/menu/{id}/ PUT   更新菜单   system:Menu:Update│ │
│ │  ☑   /api/system/menu/{id}/ DELETE 删除菜单   system:Menu:Delete│ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ▶ UserViewSet (用户管理)                               ▼│ │
│ │  ☑   /api/system/user/    GET    列表查询   system:User:List│ │
│ │  ☐   /api/system/user/    POST   新增用户   system:User:Create│ │
│ │  ☑   /api/system/user/{id}/ PUT   更新用户   system:User:Update│ │
│ └─────────────────────────────────────────────────────────┘ │
│ [全选] [取消全选]                        [取消] [确认生成]  │
└─────────────────────────────────────────────────────────────┘
```

- **交互：**
  - ViewSet 行可折叠/展开
  - 每个 ViewSet 头部有全选/取消全选
  - 表格中 name 和 value 列支持**行内编辑**（点击单元格变为输入框）
  - 已存在的记录（is_existing=true）行显示灰色背景，勾选框默认不勾中
  - 底部显示已选择数量

### 4.4 新增接口调用

```typescript
// 获取可扫描的 app 列表
export const scanGetApps = () =>
  request({ url: '/api/system/menu_button/scan_get_apps/', method: 'get' })

// 扫描指定 app
export const scanViewSet = (app: string) =>
  request({ url: '/api/system/menu_button/scan_viewset/', method: 'post', data: { app } })

// 批量创建按钮
export const scanBatchCreate = (menuId: number, buttons: any[]) =>
  request({ url: '/api/system/menu_button/scan_batch_create/', method: 'post', data: { menu_id: menuId, buttons } })
```

---

## 5. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 选中菜单后未勾选任何接口 | 确认按钮禁用，提示"请至少选择一项" |
| App 下无 ViewSet | 弹窗提示"该 App 下未检测到 ViewSet" |
| 批量创建部分失败（如 value 重复） | 返回成功数量和跳过数量，前端提示"已创建 N 项，跳过 N 项（已存在）" |
| 后端扫描异常 | 弹窗显示错误信息 |

---

## 6. 权限控制

- 该功能仅限**超级管理员**使用
- 普通管理员无权限访问新增的 3 个 API
- 前端按钮在无权限时隐藏

---

## 7. 文件清单

### 后端新增

| 文件 | 内容 |
|------|------|
| `dvadmin/system/views/menu_button.py` | 新增 3 个 action：scan_get_apps、scan_viewset、scan_batch_create |
| `dvadmin/system/urls.py` | 注册新路由 |
| `dvadmin/system/serializers/menu_button.py` | 新增扫描相关 serializer |

### 前端新增/修改

| 文件 | 内容 |
|------|------|
| `web/src/api/system/menu.ts` | 新增 3 个 API 方法 |
| `web/src/views/system/menu/index.vue` | 添加"自动扫描"按钮 |
| `web/src/views/system/menu/components/ScanModal.vue` | **新增**：扫描配置 + 预览弹窗组件 |

---

## 8. 实施顺序

1. **后端** - 完成 ViewSet 扫描算法，实现 3 个 API
2. **后端** - 注册路由
3. **前端** - 添加 API 调用
4. **前端** - 实现 ScanModal 组件（配置弹窗 + 预览表格 + 行内编辑）
5. **前端** - 在菜单管理页面集成"自动扫描"按钮
6. **测试** - 手动测试各 app 扫描效果
