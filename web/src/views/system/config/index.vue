<template>
	<fs-page>
		<div class="container">
			<header>
				<div class="buttons-group">
					<el-button type="primary" :icon="FolderAdd" @click="tabsDrawer = true">
						{{ $t('message.pages.config.buttons.addGroup') }}
					</el-button>
					<el-button type="warning" :icon="Edit" @click="contentDrawer = true">
						{{ $t('message.pages.config.buttons.addContent') }}
					</el-button>
					<el-button type="danger" :icon="Delete" @click="handleDeleteGroup">
						{{ $t('message.pages.config.buttons.deleteGroup') }}
					</el-button>
				</div>
				<div class="search-box">
					<el-input
						v-model="searchQuery"
						:placeholder="$t('message.pages.config.header.searchPlaceholder')"
						clearable
						prefix-icon="Search"
					/>
				</div>
			</header>

			<div class="filters">
				<el-button
					v-for="tab in editableTabs"
					:key="tab.key"
					:type="editableTabsValue === tab.key ? 'primary' : 'default'"
					@click="editableTabsValue = tab.key"
					class="filter-btn"
				>
					{{ tab.title_i18n || tab.title }}
				</el-button>
			</div>

			<div class="config-grid">
				<div
					v-for="item in filteredFormList"
					:key="item.id"
					class="config-card"
				>
					<div class="card-header">
						<div class="card-title">{{ item.title_i18n || item.title }}</div>
						<el-tag size="small" :type="getTagType(item.form_item_type_label)">
							{{ getLabel(item.form_item_type_label) }}
						</el-tag>
					</div>
					<div class="card-content">
						<!-- Key 信息 -->
						<div class="card-meta">
							<el-icon><Key /></el-icon>
							<span class="meta-key">{{ editableTabsValue }}.{{ item.key }}</span>
						</div>
						
						<!-- 值展示区 -->
						<div class="card-value">
							<span v-if="item.form_item_type_label === 'switch'" class="switch-value">
								<el-switch
									v-model="formData[item.key]"
									active-color="#13ce66"
									inactive-color="#ff4949"
									@change="handleConfigChange(item)"
								/>
							</span>
							<span v-else class="text-value">{{ displayValue(item) }}</span>
						</div>
						
						<!-- 额外信息展示 -->
						<div class="card-extra-info" v-if="item.placeholder || item.rule">
							<el-divider style="margin: 12px 0" />
							<div class="info-row" v-if="item.placeholder">
								<span class="info-label">提示:</span>
								<span class="info-value">{{ item.placeholder }}</span>
							</div>
							<div class="info-row" v-if="item.rule && item.rule.length > 0">
								<span class="info-label">校验:</span>
								<div class="rule-tags">
									<el-tag 
										v-for="(rule, index) in parseRules(item.rule)" 
										:key="index" 
										size="small" 
										type="warning"
									>
										{{ getRuleLabel(rule) }}
									</el-tag>
								</div>
							</div>
						</div>
					</div>
					<div class="card-footer">
						<div class="actions">
							<el-button type="primary" link :icon="Edit" @click="handleEdit(item)">
								{{ $t('message.pages.config.buttons.edit') }}
							</el-button>
							<el-button type="danger" link :icon="Delete" @click="handleDelete(item)">
								{{ $t('message.pages.config.buttons.delete') }}
							</el-button>
						</div>
					</div>
				</div>
			</div>

			<!-- 新增分组抽屉 -->
			<el-drawer
				v-model="tabsDrawer"
				:title="$t('message.pages.config.dialog.addGroup')"
				direction="rtl"
				size="30%"
			>
				<addTabs @success="handleTabsSuccess"></addTabs>
			</el-drawer>

			<!-- 新增内容抽屉 -->
			<el-drawer
				v-model="contentDrawer"
				:title="$t('message.pages.config.dialog.addContent')"
				direction="rtl"
				size="30%"
			>
				<addContent @success="handleContentSuccess"></addContent>
			</el-drawer>
		</div>
	</fs-page>
</template>

<script lang="ts" setup name="config">
import { useI18n } from 'vue-i18n';
import { Edit, FolderAdd, Delete, Key } from '@element-plus/icons-vue';
import * as api from './api';
import addTabs from './components/addTabs.vue';
import addContent from './components/addContent.vue';
import { ref, onMounted, watch, computed } from 'vue';
import { storeToRefs } from 'pinia';
import pinia from '/@/stores/index';
import { useThemeConfig } from '/@/stores/themeConfig';
import { ElMessage, ElMessageBox } from 'element-plus';

let tabsDrawer = ref(false);
let contentDrawer = ref(false);
let editableTabsValue = ref('base');
let editableTabs: any = ref([]);
let formList = ref<any[]>([]);
let formData = ref<any>({});
let searchQuery = ref('');

const { t } = useI18n();
const { themeConfig } = storeToRefs(useThemeConfig(pinia));

// 获取标签类型
const getTagType = (type: string) => {
	const typeMap: any = {
		'switch': 'success',
		'select': 'warning',
		'radio': 'primary',
		'checkbox': 'info',
		'text': 'info',
		'textarea': 'info',
		'number': 'danger',
		'img': 'warning',
		'imgs': 'warning',
	};
	return typeMap[type] || 'info';  // 默认使用 info,避免空字符串
};

// 获取类型标签
const getLabel = (type: string) => {
	const labelMap: any = {
		'switch': '开关',
		'select': '下拉',
		'radio': '单选',
		'checkbox': '多选',
		'text': '文本',
		'textarea': '长文本',
		'number': '数字',
		'img': '图片',
		'imgs': '多图片',
	};
	return labelMap[type] || type;
};

// 解析校验规则
const parseRules = (rule: any) => {
	if (!rule) return [];
	try {
		// rule 可能是字符串或数组
		if (typeof rule === 'string') {
			return [JSON.parse(rule)];
		}
		if (Array.isArray(rule)) {
			return rule;
		}
		return [rule];
	} catch (e) {
		return [];
	}
};

// 获取校验规则标签
const getRuleLabel = (rule: any) => {
	if (!rule) return '';
	if (rule.required) return '必填';
	if (rule.type === 'email') return '邮箱';
	if (rule.type === 'url') return 'URL';
	if (rule.type === 'number') return '数字';
	return '自定义';
};

// 显示值
const displayValue = (item: any) => {
	const value = formData.value[item.key];
	if (value === null || value === undefined) return '-';
	if (Array.isArray(value)) return value.join(', ');
	return String(value);
};

// 过滤后的配置列表
const filteredFormList = computed(() => {
	if (!searchQuery.value) return formList.value;
	const query = searchQuery.value.toLowerCase();
	return formList.value.filter(item => 
		(item.title_i18n || item.title).toLowerCase().includes(query) ||
		item.key.toLowerCase().includes(query)
	);
});

// 获取配置列表
const getFormList = () => {
	api.GetDetail(editableTabsValue.value, themeConfig.value.globalI18n).then((res: any) => {
		formList.value = res.data || [];
		formData.value = {};
		formList.value.forEach(item => {
			formData.value[item.key] = item.value;
		});
	});
};

// 获取Tab列表
const getTabs = () => {
	api
		.GetList({
			limit: 999,
			parent__isnull: true,
			language: themeConfig.value.globalI18n,
		})
		.then((res: any) => {
			let data = res.data;
			editableTabs.value = data;
			if (data.length > 0 && !editableTabsValue.value) {
				editableTabsValue.value = data[0].key;
			}
			getFormList();
		});
};

// 处理配置变更
const handleConfigChange = async (item: any) => {
	try {
		await api.UpdateObj({
			id: item.id,
			value: formData.value[item.key]
		});
		ElMessage.success(t('message.pages.config.messages.updateSuccess'));
	} catch (error) {
		// 重新获取数据以恢复原值
		getFormList();
		ElMessage.error(t('message.pages.config.messages.updateFailed'));
	}
};

// 编辑配置
const handleEdit = (item: any) => {
	contentDrawer.value = true;
	// TODO: 传递编辑参数
};

// 删除配置
const handleDelete = (item: any) => {
	ElMessageBox.confirm(
		t('message.pages.config.messages.deleteConfirm'),
		t('message.pages.config.buttons.delete'),
		{
			confirmButtonText: t('message.pages.config.buttons.confirm'),
			cancelButtonText: t('message.pages.config.buttons.cancel'),
			type: 'warning',
		}
	).then(async () => {
		try {
			await api.DelObj(item.id);
			ElMessage.success(t('message.pages.config.messages.deleteSuccess'));
			getFormList();
		} catch (error) {
			ElMessage.error(t('message.pages.config.messages.deleteFailed'));
		}
	}).catch(() => {});
};

// Tab添加成功
const handleTabsSuccess = () => {
	tabsDrawer.value = false;
	getTabs();
};

// 内容添加成功
const handleContentSuccess = () => {
	contentDrawer.value = false;
	getFormList();
};

// 删除当前分组
const handleDeleteGroup = () => {
	ElMessageBox.confirm(
		t('message.pages.config.messages.deleteGroupConfirm'),
		t('message.pages.config.buttons.deleteGroup'),
		{
			confirmButtonText: t('message.pages.config.buttons.confirm'),
			cancelButtonText: t('message.pages.config.buttons.cancel'),
			type: 'warning',
		}
	).then(async () => {
		try {
			// 查找当前分组的ID
			const currentGroup = editableTabs.value.find((tab: any) => tab.key === editableTabsValue.value);
			if (!currentGroup) {
				ElMessage.error(t('message.pages.config.messages.groupNotFound'));
				return;
			}
			
			await api.DelObj(currentGroup.id);
			ElMessage.success(t('message.pages.config.messages.deleteGroupSuccess'));
			
			// 重新获取分组列表
			await getTabs();
			
			// 如果分组列表不为空,切换到第一个分组
			if (editableTabs.value.length > 0) {
				editableTabsValue.value = editableTabs.value[0].key;
			}
		} catch (error) {
			ElMessage.error(t('message.pages.config.messages.deleteGroupFailed'));
		}
	}).catch(() => {});
};

onMounted(() => {
	getTabs();
});

// 语言切换时刷新
watch(
	() => themeConfig.value.globalI18n,
	() => {
		getTabs();
	}
);

// Tab切换时刷新配置列表
watch(editableTabsValue, () => {
	getFormList();
});
</script>

<style scoped>
.container {
	max-width: 100%;
	margin: 0 auto;
	padding: 20px;
}

header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 30px;
}

.buttons-group {
	display: flex;
	align-items: center;
	gap: 12px;
}

.search-box {
	width: 300px;
}

.filters {
	display: flex;
	gap: 12px;
	margin-bottom: 25px;
	flex-wrap: wrap;
}

.filter-btn {
	padding: 8px 20px;
	border-radius: 20px;
	transition: all 0.3s ease;
}

.config-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
	gap: 25px;
}

.config-card {
	background: var(--el-bg-color);
	border-radius: 12px;
	overflow: hidden;
	box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
	transition: transform 0.3s ease, box-shadow 0.3s ease;
	border: 1px solid var(--el-border-color-lighter);
}

.config-card:hover {
	transform: translateY(-5px);
	box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

.card-header {
	padding: 20px;
	border-bottom: 1px solid var(--el-border-color-lighter);
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.card-title {
	font-size: 18px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.card-content {
	padding: 20px;
}

.card-meta {
	display: flex;
	align-items: center;
	color: var(--el-text-color-secondary);
	font-size: 14px;
	margin-bottom: 15px;
	gap: 6px;
}

.meta-key {
	font-family: 'Courier New', monospace;
	background: var(--el-fill-color);
	padding: 2px 8px;
	border-radius: 4px;
	font-size: 13px;
}

.card-value {
	color: var(--el-text-color-regular);
	line-height: 1.6;
	min-height: 40px;
	display: flex;
	align-items: center;
}

.switch-value {
	display: flex;
	align-items: center;
}

.text-value {
	word-break: break-all;
}

/* 额外信息展示区 */
.card-extra-info {
	margin-top: 12px;
}

.info-row {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 8px;
	font-size: 13px;
}

.info-row:last-child {
	margin-bottom: 0;
}

.info-label {
	color: var(--el-text-color-secondary);
	font-weight: 500;
	min-width: 40px;
}

.info-value {
	color: var(--el-text-color-regular);
	flex: 1;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.rule-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
	flex: 1;
}

.card-footer {
	padding: 15px 20px;
	background: var(--el-fill-color-lighter);
	display: flex;
	justify-content: flex-end;
	align-items: center;
}

.actions {
	display: flex;
	gap: 12px;
}

@media (max-width: 768px) {
	.config-grid {
		grid-template-columns: 1fr;
	}

	header {
		flex-direction: column;
		align-items: flex-start;
	}

	.search-box {
		width: 100%;
	}

	.filters {
		width: 100%;
	}
}
</style>
