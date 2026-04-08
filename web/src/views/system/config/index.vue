<template>
	<el-card>
		<div>
			<el-header>
				<div class="yxt-flex-between">
					<div>
						<el-tag>{{ $t('message.pages.config.header.tagText') }}</el-tag>
					</div>
					<div>
						<el-button-group>
							<el-button type="primary" size="small" :icon="FolderAdd" @click="tabsDrawer = true"> {{ $t('message.pages.config.buttons.addGroup') }} </el-button>
							<el-button size="small" type="warning" :icon="Edit" @click="contentDrawer = true"> {{ $t('message.pages.config.buttons.addContent') }} </el-button>
						</el-button-group>
					</div>
				</div>
			</el-header>
		</div>
		<div>
			<el-drawer v-if="tabsDrawer" :title="$t('message.pages.config.dialog.addGroup')" v-model="tabsDrawer" direction="rtl" size="30%">
				<addTabs></addTabs>
			</el-drawer>
		</div>
		<div>
			<el-drawer v-if="contentDrawer" :title="$t('message.pages.config.dialog.addContent')" v-model="contentDrawer" direction="rtl" size="30%">
				<addContent></addContent>
			</el-drawer>
		</div>
		<el-tabs type="border-card" v-model="editableTabsValue">
			<el-tab-pane :key="index" v-for="(item, index) in editableTabs" :label="item.title_i18n || item.title" :name="item.key">
				<span slot="label" v-if="item.icon"><i :class="item.icon" style="font-weight: 1000; font-size: 16px"></i></span>
				<el-row v-if="item.icon">
					<el-col :offset="4" :span="8">
						<addContent></addContent>
					</el-col>
				</el-row>
				<formContent v-else :options="item" :editableTabsItem="item"></formContent>
			</el-tab-pane>
		</el-tabs>
	</el-card>
</template>

<script lang="ts" setup name="config">
import { useI18n } from 'vue-i18n';
import { Edit, FolderAdd } from '@element-plus/icons-vue';
import * as api from './api';
import addTabs from './components/addTabs.vue';
import addContent from './components/addContent.vue';
import formContent from './components/formContent.vue';
import { ref, onMounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import pinia from '/@/stores/index';
import { useThemeConfig } from '/@/stores/themeConfig';
let tabsDrawer = ref(false);
let contentDrawer = ref(false);
let editableTabsValue = ref('base');
let editableTabs: any = ref([]);

const { t } = useI18n();
const { themeConfig } = storeToRefs(useThemeConfig(pinia));

const getTabs = () => {
	api
		.GetList({
			limit: 999,
			parent__isnull: true,
			language: themeConfig.value.globalI18n,
		})
		.then((res: any) => {
			let data = res.data;
			data.push({
				title: t('message.pages.config.tabs.none'),
				title_i18n: t('message.pages.config.tabs.none'),
				icon: 'el-icon-plus',
				key: 'null',
			});
			editableTabs.value = data;
		});
};

onMounted(() => {
	getTabs();
});

// 语言切换时刷新 Tab 标签
watch(
	() => themeConfig.value.globalI18n,
	() => {
		getTabs();
	}
);
</script>

<style>
/*用 flex  两边对齐*/
.yxt-flex-between {
	display: flex;
	justify-content: space-between;
}
</style>
