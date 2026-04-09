# API 权限自动扫描与批量生成 - 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在菜单管理页面为管理员提供自动扫描 Django app 下所有 ViewSet 接口、一键预览并批量生成 MenuButton 权限记录的功能。

**Architecture:** 后端新增 3 个 DRF action（获取 App 列表 / 扫描 ViewSet / 批量创建），前端新增 ScanModal 组件实现 App 选择、接口预览（分组表格+行内编辑）、确认生成的完整流程。

**Tech Stack:** Django REST Framework (ViewSet/Router), Vue 3 + Element Plus + TypeScript + FastCRUD

---

## 文件结构

```
backend/dvadmin/system/views/menu_button.py     # 新增 3 个 action
frontend/web/src/views/system/menu/api.ts        # 新增 3 个 API 调用
frontend/web/src/views/system/menu/index.vue     # 添加"自动扫描"按钮 + 引用 ScanModal
frontend/web/src/views/system/menu/components/ScanModal/index.vue  # 新增：扫描配置+预览弹窗
```

---

## Task 1: 后端 - 实现 ViewSet 扫描算法（核心逻辑）

**Files:**
- Modify: `backend/dvadmin/system/views/menu_button.py` (在 MenuButtonViewSet 末尾新增扫描相关方法)

- [ ] **Step 1: 在 menu_button.py 中添加 scan_get_apps action**

在 `MenuButtonViewSet` 类末尾（在 `batch_create` 方法之后）添加以下代码：

```python
@action(methods=['get'], detail=False, permission_classes=[IsAuthenticated])
def scan_get_apps(self, request):
    """
    获取可扫描的 Django App 列表
    仅返回 dvadmin 下的自定义 app（排除框架内置 app）
    """
    from django.apps import apps
    from dvadmin.system.models import MenuButton

    # 获取 dvadmin 下所有已注册的自定义 app
    custom_apps = []
    for app_config in apps.get_app_configs():
        if app_config.name.startswith('dvadmin.') and app_config.name != 'dvadmin':
            # 排除 system app 本身（避免循环）
            if app_config.name != 'dvadmin.system':
                custom_apps.append(app_config.name.split('.')[-1])

    return DetailResponse(data=sorted(custom_apps))
```

- [ ] **Step 2: 添加 scan_viewset action（扫描核心逻辑）**

在同一文件 `MenuButtonViewSet` 类中继续添加：

```python
@action(methods=['post'], detail=False, permission_classes=[IsAuthenticated])
def scan_viewset(self, request):
    """
    扫描指定 app 下所有 ViewSet，返回接口预览数据
    请求体: {"app": "system"}
    """
    import importlib
    from rest_framework.routers import SimpleRouter, DefaultRouter
    from rest_framework.viewsets import GenericViewSet, ModelViewSet
    from dvadmin.system.models import MenuButton

    app_name = request.data.get('app')
    if not app_name:
        return DetailResponse(data=[], msg="app 参数必填")

    full_app_name = f'dvadmin.{app_name}'
    result = []

    try:
        # 动态导入 app 下的 views 模块
        views_module = importlib.import_module(f'{full_app_name}.views')
    except ModuleNotFoundError:
        return DetailResponse(data=[], msg=f"App '{app_name}' 下未找到 views 模块")

    # 获取已存在的 value 集合
    existing_values = set(MenuButton.objects.values_list('value', flat=True))

    # 遍历 app 下所有 ViewSet 类
    for attr_name in dir(views_module):
        cls = getattr(views_module, attr_name)
        if not isinstance(cls, type):
            continue
        if not issubclass(cls, GenericViewSet):
            continue
        if cls is GenericViewSet:
            continue

        # 提取 ViewSet 名称
        viewset_name = cls.__name__  # 如 "MenuViewSet"
        if viewset_name.endswith('ViewSet'):
            model_name = viewset_name[:-8]  # "Menu"
        else:
            model_name = viewset_name

        # 尝试从 docstring 获取中文名称
        viewset_verbose_name = cls.__doc__.strip().split('\n')[0] if cls.__doc__ else viewset_name

        # 构建该 ViewSet 的 router 来获取所有 action
        router = SimpleRouter()
        router.register(viewset_name.lower().replace('viewset', ''), cls, basename=viewset_name.lower())

        buttons = []
        for prefix, viewset_instance, actions in router.registry:
            for action, method in actions.items():
                # 获取 HTTP 方法
                http_method = method.upper()  # 如 "GET", "POST"

                # 映射 HTTP 方法到 method 字段
                method_map = {'GET': 0, 'POST': 1, 'PUT': 2, 'PATCH': 2, 'DELETE': 3}
                method_int = method_map.get(http_method, 0)

                # 获取 action 名称（驼峰转首字母大写）
                action_title = action.title().replace('_', '')
                value = f"{app_name}:{model_name}:{action_title}"

                # 获取 docstring 作为 name
                action_method = getattr(viewset_instance, action, None)
                if action_method and hasattr(action_method, '__doc__') and action_method.__doc__:
                    name = action_method.__doc__.strip().split('\n')[0]
                else:
                    # 固定规则
                    name_map = {
                        'List': '列表查询', 'Retrieve': '详情查询', 'Create': '新增',
                        'Update': '更新', 'Destroy': '删除', 'PartialUpdate': '部分更新',
                    }
                    name = name_map.get(action_title, action_title)

                # 生成接口路径
                lookup = 'pk'
                if hasattr(viewset_instance, 'lookup_field'):
                    lookup = viewset_instance.lookup_field or 'pk'
                if action in ('list', 'create'):
                    path = f"/api/{app_name}/{prefix}/"
                elif action in ('retrieve', 'update', 'partial_update', 'destroy'):
                    path = f"/api/{app_name}/{prefix}/{{{lookup}}}/"
                else:
                    # custom action
                    path = f"/api/{app_name}/{prefix}/{action}/"

                buttons.append({
                    'path': path,
                    'method': http_method,
                    'action': action,
                    'name': name,
                    'value': value,
                    'is_existing': value in existing_values,
                    'method_int': method_int,
                })

        if buttons:
            result.append({
                'viewset': viewset_name,
                'viewset_verbose_name': viewset_verbose_name,
                'buttons': buttons,
            })

    return DetailResponse(data=result)
```

- [ ] **Step 3: 添加 scan_batch_create action（批量创建）**

```python
@action(methods=['post'], detail=False, permission_classes=[IsAuthenticated])
def scan_batch_create(self, request):
    """
    批量创建 MenuButton
    请求体: {"menu_id": 12, "buttons": [...]}
    """
    from dvadmin.system.models import MenuButton

    menu_id = request.data.get('menu_id')
    buttons = request.data.get('buttons', [])

    if not menu_id:
        return DetailResponse(data={}, msg="menu_id 参数必填", code=4000)
    if not buttons:
        return DetailResponse(data={}, msg="buttons 不能为空", code=4000)

    created_count = 0
    skipped_count = 0

    # 获取已存在的 value
    existing_values = set(MenuButton.objects.filter(menu_id=menu_id).values_list('value', flat=True))

    objects_to_create = []
    for btn in buttons:
        value = btn.get('value')
        if value in existing_values:
            skipped_count += 1
            continue

        method_int = btn.get('method_int', 0)
        if isinstance(btn.get('method'), str):
            method_map = {'GET': 0, 'POST': 1, 'PUT': 2, 'PATCH': 2, 'DELETE': 3}
            method_int = method_map.get(btn['method'].upper(), 0)

        objects_to_create.append(MenuButton(
            menu_id=menu_id,
            name=btn.get('name', ''),
            value=value,
            api=btn.get('path', ''),
            method=method_int,
        ))
        existing_values.add(value)

    if objects_to_create:
        MenuButton.objects.bulk_create(objects_to_create)
        created_count = len(objects_to_create)

    return DetailResponse(data={'count': created_count, 'skipped': skipped_count}, msg=f"已创建 {created_count} 项，跳过 {skipped_count} 项（已存在）")
```

- [ ] **Step 4: 验证文件语法**

Run: `cd /Users/hongzai/工程/工作/AVC/django-vue3-admin/backend && python -c "from dvadmin.system.views.menu_button import MenuButtonViewSet; print('OK')"`
Expected: 输出 "OK"，无报错

- [ ] **Step 5: 提交**

```bash
cd /Users/hongzai/工程/工作/AVC/django-vue3-admin
git add backend/dvadmin/system/views/menu_button.py
git commit -m "feat(permission): add ViewSet scan APIs for auto permission generation"
```

---

## Task 2: 后端 - 注册路由

**Files:**
- Modify: `backend/dvadmin/system/urls.py` (无需修改，使用 ViewSet 的 @action 装饰器自动注册)

- [ ] **Step 1: 确认路由自动注册**

`MenuButtonViewSet` 已通过 `system_url.register(r'menu_button', MenuButtonViewSet)` 注册，其 `@action` 装饰的方法会自动生成子路由：
- `scan_get_apps` → `/api/system/menu_button/scan_get_apps/`
- `scan_viewset` → `/api/system/menu_button/scan_viewset/`
- `scan_batch_create` → `/api/system/menu_button/scan_batch_create/`

无需修改 urls.py，提交确认即可：

```bash
git add -u
git commit -m "chore: confirm route auto-registration (no urls.py changes needed)"
```

---

## Task 3: 前端 - 添加 API 调用

**Files:**
- Modify: `web/src/views/system/menu/api.ts` (在末尾追加 3 个导出函数)

- [ ] **Step 1: 在 api.ts 末尾追加扫描相关 API 调用**

打开 `/Users/hongzai/工程/工作/AVC/django-vue3-admin/web/src/views/system/menu/api.ts`，在 `menuMoveDown` 函数之后（最后一个 export 之后）添加：

```typescript
/**
 * 获取可扫描的 Django App 列表
 */
export function scanGetApps() {
  return request({
    url: '/api/system/menu_button/scan_get_apps/',
    method: 'get',
  });
}

/**
 * 扫描指定 app 下的 ViewSet 接口
 */
export function scanViewSet(app: string) {
  return request({
    url: '/api/system/menu_button/scan_viewset/',
    method: 'post',
    data: { app },
  });
}

/**
 * 批量创建菜单按钮权限
 */
export function scanBatchCreate(menuId: number | string, buttons: any[]) {
  return request({
    url: '/api/system/menu_button/scan_batch_create/',
    method: 'post',
    data: { menu_id: menuId, buttons },
  });
}
```

- [ ] **Step 2: 验证 TypeScript 语法**

Run: `cd /Users/hongzai/工程/工作/AVC/django-vue3-admin/web && npx tsc --noEmit src/views/system/menu/api.ts 2>&1 | head -20`
Expected: 无报错或仅类型警告

- [ ] **Step 3: 提交**

```bash
git add web/src/views/system/menu/api.ts
git commit -m "feat(menu): add scan APIs for auto permission generation"
```

---

## Task 4: 前端 - 实现 ScanModal 组件

**Files:**
- Create: `web/src/views/system/menu/components/ScanModal/index.vue` (新增)

- [ ] **Step 1: 创建 ScanModal 组件文件**

创建目录和文件：`/Users/hongzai/工程/工作/AVC/django-vue3-admin/web/src/views/system/menu/components/ScanModal/index.vue`

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    :width="dialogWidth"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <!-- 第一步：选择 App -->
    <div v-if="step === 1" class="scan-step1">
      <el-form label-width="100px">
        <el-form-item :label="$t('message.pages.menu.scan.targetApp')">
          <el-select
            v-model="selectedApp"
            :placeholder="$t('message.pages.menu.scan.selectAppPlaceholder')"
            filterable
            style="width: 100%"
            @change="handleAppChange"
          >
            <el-option
              v-for="app in appList"
              :key="app"
              :label="app"
              :value="app"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <!-- 第二步：扫描结果预览 -->
    <div v-else-if="step === 2" class="scan-step2">
      <div class="step2-header">
        <span>{{ $t('message.pages.menu.scan.targetApp') }}: <strong>{{ selectedApp }}</strong></span>
        <span>{{ $t('message.pages.menu.scan.selectedCount', { count: selectedCount }) }}</span>
      </div>

      <el-table
        :data="tableData"
        border
        style="width: 100%; margin-top: 12px"
        max-height="500"
        size="small"
      >
        <el-table-column type="selection" width="45" fixed />
        <el-table-column prop="viewset" :label="$t('message.pages.menu.scan.viewset')" width="180">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.viewset }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" :label="$t('message.pages.menu.scan.path')" min-width="200" />
        <el-table-column prop="method" :label="$t('message.pages.menu.scan.method')" width="80">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="methodTagType(row.method)"
              effect="plain"
            >{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('message.pages.menu.scan.name')" min-width="140">
          <template #default="{ row }">
            <el-input
              v-if="row._editing"
              v-model="row._editName"
              size="small"
              @blur="row._editName = row._editName; row._editing = false"
              @keyup.enter="row._editName = row._editName; row._editing = false"
            />
            <span v-else class="cell-editable" @click="startEdit(row, 'name')">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('message.pages.menu.scan.value')" min-width="160">
          <template #default="{ row }">
            <el-input
              v-if="row._editingValue"
              v-model="row._editValue"
              size="small"
              @blur="row._editValue = row._editValue; row._editingValue = false"
              @keyup.enter="row._editValue = row._editValue; row._editingValue = false"
            />
            <span v-else class="cell-editable" @click="startEdit(row, 'value')">{{ row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('message.pages.menu.scan.status')" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_existing" type="info" size="small">{{ $t('message.pages.menu.scan.existing') }}</el-tag>
            <el-tag v-else type="success" size="small">{{ $t('message.pages.menu.scan.new') }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">{{ $t('message.pages.menu.buttons.cancel') }}</el-button>
        <el-button v-if="step === 2" @click="step = 1">{{ $t('message.pages.menu.scan.back') }}</el-button>
        <el-button
          v-if="step === 1"
          type="primary"
          :loading="scanning"
          :disabled="!selectedApp"
          @click="handleScan"
        >
          {{ $t('message.pages.menu.scan.startScan') }}
        </el-button>
        <el-button
          v-else
          type="primary"
          :loading="submitting"
          :disabled="selectedCount === 0"
          @click="handleSubmit"
        >
          {{ $t('message.pages.menu.scan.confirmGenerate') }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { scanGetApps, scanViewSet, scanBatchCreate } from '../../api';

const props = defineProps<{
  modelValue: boolean;
  menuId: number | null;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
  (e: 'success'): void;
}>();

// --- 状态 ---
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const step = ref(1);
const dialogTitle = computed(() => step.value === 1
  ? '自动扫描接口权限'
  : '扫描结果预览'
);
const dialogWidth = computed(() => step.value === 1 ? '500px' : '90%');

const appList = ref<string[]>([]);
const selectedApp = ref('');
const scanning = ref(false);
const submitting = ref(false);
const tableData = ref<any[]>([]);

// --- 计算属性 ---
const selectedCount = computed(() => {
  return tableData.value.filter(row => !row.is_existing).length;
});

// --- 方法 ---
const methodTagType = (method: string) => {
  const map: Record<string, any> = {
    GET: 'success', POST: 'primary', PUT: 'warning', PATCH: 'warning', DELETE: 'danger',
  };
  return map[method] || 'info';
};

const startEdit = (row: any, field: 'name' | 'value') => {
  if (row.is_existing) return;
  if (field === 'name') {
    row._editName = row.name;
    row._editing = true;
  } else {
    row._editValue = row.value;
    row._editingValue = true;
  }
};

const loadApps = async () => {
  try {
    const res: any = await scanGetApps();
    appList.value = res.data || [];
  } catch {
    appList.value = [];
  }
};

const handleAppChange = () => {
  // 重置第二步
  step.value = 1;
  tableData.value = [];
};

const handleScan = async () => {
  if (!selectedApp.value) return;
  scanning.value = true;
  try {
    const res: any = await scanViewSet(selectedApp.value);
    const flatData: any[] = [];
    for (const group of (res.data || [])) {
      for (const btn of group.buttons) {
        flatData.push({
          ...btn,
          _editing: false,
          _editName: btn.name,
          _editingValue: false,
          _editValue: btn.value,
        });
      }
    }
    tableData.value = flatData;
    if (flatData.length === 0) {
      ElMessage.warning('该 App 下未检测到 ViewSet 接口');
    } else {
      step.value = 2;
    }
  } catch (err: any) {
    ElMessage.error(err?.message || '扫描失败');
  } finally {
    scanning.value = false;
  }
};

const handleSubmit = async () => {
  if (!props.menuId) {
    ElMessage.warning('未选中菜单');
    return;
  }
  const selected = tableData.value
    .filter(row => !row.is_existing)
    .map(row => ({
      path: row.path,
      method: row.method,
      action: row.action,
      name: row._editName || row.name,
      value: row._editValue || row.value,
      method_int: row.method_int,
    }));

  if (selected.length === 0) {
    ElMessage.warning('请至少选择一项');
    return;
  }

  submitting.value = true;
  try {
    const res: any = await scanBatchCreate(props.menuId, selected);
    ElMessage.success(res?.msg || `已创建 ${selected.length} 项`);
    emit('success');
    handleClose();
  } catch (err: any) {
    ElMessage.error(err?.message || '创建失败');
  } finally {
    submitting.value = false;
  }
};

const handleClose = () => {
  visible.value = false;
  step.value = 1;
  selectedApp.value = '';
  tableData.value = [];
};

// 打开时加载 app 列表
const handleOpen = async () => {
  await loadApps();
};

defineExpose({ handleOpen });
</script>

<style scoped lang="scss">
.scan-step1 {
  padding: 20px 0;
}

.scan-step2 {
  .step2-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #606266;
  }
}

.cell-editable {
  cursor: pointer;
  &:hover {
    color: var(--el-color-primary);
    text-decoration: underline;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
```

- [ ] **Step 2: 创建 index.ts 导出文件**

创建 `web/src/views/system/menu/components/ScanModal/index.ts`：

```typescript
export { default } from './index.vue';
```

- [ ] **Step 3: 提交**

```bash
mkdir -p web/src/views/system/menu/components/ScanModal
# 写入上述两个文件后
git add web/src/views/system/menu/components/ScanModal/
git commit -m "feat(menu): add ScanModal component for auto permission generation"
```

---

## Task 5: 前端 - 集成自动扫描按钮到菜单管理页面

**Files:**
- Modify: `web/src/views/system/menu/index.vue`

- [ ] **Step 1: 在 index.vue 中引入 ScanModal 并添加按钮**

在 `<script lang="ts" setup>` 部分：

**修改前（import 部分）：**
```typescript
import MenuTreeCom from './components/MenuTreeCom/index.vue';
import MenuButtonCom from './components/MenuButtonCom/index.vue';
import MenuFormCom from './components/MenuFormCom/index.vue';
import MenuFieldCom from './components/MenuFieldCom/index.vue';
```

**修改后：**
```typescript
import MenuTreeCom from './components/MenuTreeCom/index.vue';
import MenuButtonCom from './components/MenuButtonCom/index.vue';
import MenuFormCom from './components/MenuFormCom/index.vue';
import MenuFieldCom from './components/MenuFieldCom/index.vue';
import ScanModal from './components/ScanModal/index.vue';
```

**添加状态变量：**
```typescript
let selectedMenuId = ref<number | null>(null);
let scanModalVisible = ref(false);
let scanModalRef = ref<any>(null);
```

**添加打开扫描弹窗的函数：**
```typescript
const handleOpenScanModal = () => {
  if (!selectedMenuId.value) {
    ElMessage.warning('请先选择一个菜单');
    return;
  }
  scanModalVisible.value = true;
  nextTick(() => {
    scanModalRef.value?.handleOpen();
  });
};

const handleScanSuccess = () => {
  // 刷新按钮列表
  menuButtonRef.value?.handleRefreshTable({ id: selectedMenuId.value });
};
```

**在 `handleTreeClick` 中更新选中菜单 ID：**
```typescript
const handleTreeClick = (record: MenuTreeItemType) => {
  selectedMenuId.value = record.id ?? null;
  menuButtonRef.value?.handleRefreshTable(record);
  menuFieldRef.value?.handleRefreshTable(record)
};
```

在 `<template>` 中的 `MenuButtonCom` 下方添加扫描按钮和 ScanModal：

在 `</el-tabs>` 之前、`<MenuFieldCom>` 之后添加：

```vue
<div class="menu-scan-btn">
  <el-button type="primary" @click="handleOpenScanModal">
    <el-icon><Monitor /></el-icon>
    自动扫描
  </el-button>
</div>

<ScanModal
  ref="scanModalRef"
  v-model="scanModalVisible"
  :menuId="selectedMenuId"
  @success="handleScanSuccess"
/>
```

在 `<style>` 中添加按钮样式：
```scss
.menu-scan-btn {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
```

还需要引入 `ElMessage`（如果没有）：
```typescript
import { ElMessage } from 'element-plus';
```

- [ ] **Step 2: 验证 Vue 组件语法**

Run: `cd /Users/hongzai/工程/工作/AVC/django-vue3-admin/web && npx vue-tsc --noEmit src/views/system/menu/index.vue 2>&1 | head -30`
Expected: 无严重错误（类型警告可忽略）

- [ ] **Step 3: 提交**

```bash
git add web/src/views/system/menu/index.vue
git commit -m "feat(menu): integrate auto-scan button and ScanModal into menu management"
```

---

## Task 6: 后端 - 添加国际化字段支持（可选增强）

**Files:**
- Modify: `backend/dvadmin/system/views/menu_button.py` 的 `scan_batch_create` 方法

- [ ] **Step 1: 在批量创建时填充 name_en 和 name_zh_tw**

在 `scan_batch_create` 的 `objects_to_create.append()` 处修改：

```python
from deep_translator import GoogleTranslator

def translate_name(name: str, target: str) -> str:
    try:
        if target == 'en':
            return GoogleTranslator(source='zh-CN', target='en').translate(name)
        else:
            return GoogleTranslator(source='zh-CN', target='zh-TW').translate(name)
    except Exception:
        return name

# 在循环中：
en_name = translate_name(btn.get('name', ''), 'en')
zh_tw_name = translate_name(btn.get('name', ''), 'zh-TW')
objects_to_create.append(MenuButton(
    menu_id=menu_id,
    name=btn.get('name', ''),
    name_en=en_name,
    name_zh_tw=zh_tw_name,
    value=value,
    api=btn.get('path', ''),
    method=method_int,
))
```

> **注意：** 此步需要先安装 `deep-translator`：`pip install deep-translator`。如果项目不想引入额外依赖，跳过此任务。

- [ ] **Step 2: 提交**

```bash
git add -u
git commit -m "feat(permission): auto-translate name_en/name_zh_tw during batch create"
```

---

## Task 7: 测试与提交

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && python manage.py runserver 0.0.0.0:8000`

- [ ] **Step 2: 测试 API 1 - 获取 App 列表**

Run: `curl -s http://localhost:8000/api/system/menu_button/scan_get_apps/ -H "Authorization: Token xxx" | python -m json.tool`
Expected: 返回 `["api", "blog", ...]` 格式的 app 名称列表

- [ ] **Step 3: 测试 API 2 - 扫描 ViewSet**

Run: `curl -s -X POST http://localhost:8000/api/system/menu_button/scan_viewset/ -H "Authorization: Token xxx" -H "Content-Type: application/json" -d '{"app":"system"}' | python -m json.tool | head -50`
Expected: 返回按 ViewSet 分组的接口列表，包含 path/method/name/value/is_existing

- [ ] **Step 4: 提交所有代码**

```bash
git add -u
git status
git commit -m "feat: complete API permission auto-scan and batch generation feature"
```

- [ ] **Step 5: 切换到新分支并推送**

```bash
git checkout -b feature/api-permission-scan
git push -u origin feature/api-permission-scan
```

---

## 实施顺序总结

| 任务 | 描述 | 依赖 |
|------|------|------|
| Task 1 | 后端 - ViewSet 扫描算法 + 3 个 API | 无 |
| Task 2 | 后端 - 路由注册（无需修改） | Task 1 |
| Task 3 | 前端 - API 调用 | Task 2 |
| Task 4 | 前端 - ScanModal 组件 | Task 3 |
| Task 5 | 前端 - 集成到菜单管理页 | Task 4 |
| Task 6 | 后端 - 国际化翻译（可选） | Task 1 |
| Task 7 | 测试 + 提 PR | Task 1-5 |
