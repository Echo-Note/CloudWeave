<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding">
			<template #actionbar-right>
				<importExcel api="api/company/entity/" v-auth="'company:Import'">{{ $t('message.pages.company.buttons.import') }}</importExcel>
			</template>
		</fs-crud>
	</fs-page>
</template>

<script lang="ts" setup name="company">
import { ref, onMounted, watch } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import { useThemeConfig } from '/@/stores/themeConfig';
import { storeToRefs } from 'pinia';
import importExcel from '/@/components/importExcel/index.vue';

const { themeConfig } = storeToRefs(useThemeConfig());

const { crudBinding, crudRef, crudExpose, resetCrudOptions } = useFs({ createCrudOptions, context: {} });

// 语言切换时重新构建 crud options
watch(
	() => themeConfig.value.globalI18n,
	() => {
		resetCrudOptions();
	}
);

// 页面打开后获取列表数据
onMounted(() => {
	crudExpose.doRefresh();
});
</script>
