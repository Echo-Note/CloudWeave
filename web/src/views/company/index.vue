<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding">
			<template #actionbar-right>
				<importExcel api="api/company/entity/" v-auth="'company:Import'">{{ $t('message.pages.company.buttons.import') }}</importExcel>
			</template>
			<!-- 营业执照列：缩略图 + 点击放大预览 -->
			<template #cell_business_license="scope">
				<div v-if="scope.row.business_license" style="display: flex; justify-content: center; align-items: center;">
					<el-image
						style="width: 60px; height: 40px;"
						fit="contain"
						:src="getBaseURL(scope.row.business_license)"
						:preview-src-list="[getBaseURL(scope.row.business_license)]"
						:preview-teleported="true"
					/>
				</div>
				<span v-else>-</span>
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
import { CheckOcrStatus } from './api';
import { getBaseURL } from '/@/utils/baseUrl';

const { themeConfig } = storeToRefs(useThemeConfig());

// OCR 是否可用（响应式状态）
const ocrAvailable = ref(false);

// 表单提交状态与初始营业执照值（用于清理未保存的文件）
const formSubmitted = ref(false);
const initialLicense = ref('');

// 当前表单中营业执照的文件 ID（上传成功时记录，供 OCR 按钮使用）
const licenseFileId = ref<number | string | null>(null);

const { crudBinding, crudRef, crudExpose, resetCrudOptions } = useFs({
	createCrudOptions,
	context: { ocrAvailable, formSubmitted, initialLicense, licenseFileId },
});

// 语言切换时重新构建 crud options
watch(
	() => themeConfig.value.globalI18n,
	() => {
		resetCrudOptions();
	}
);

// 页面打开后检测 OCR 可用性并加载数据
onMounted(async () => {
	try {
		const res = await CheckOcrStatus();
		ocrAvailable.value = !!(res as any).data?.available;
	} catch {
		ocrAvailable.value = false;
	}
	crudExpose.doRefresh();
});
</script>
