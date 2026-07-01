<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding">
			<template #actionbar-right>
				<importExcel api="api/cloud/registrar/" v-auth="'cloud_registrar:Import'">导入</importExcel>
			</template>
		</fs-crud>
	</fs-page>
</template>

<script lang="ts" setup name="cloud_registrar">
import { onMounted } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import importExcel from '/@/components/importExcel/index.vue';

const { crudBinding, crudRef, crudExpose, resetCrudOptions } = useFs({
	createCrudOptions,
	context: {},
});

onMounted(() => {
	crudExpose.doRefresh();
});
</script>
