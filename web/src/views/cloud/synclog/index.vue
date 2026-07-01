<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding" />
	</fs-page>
</template>

<script lang="ts" setup name="cloud_synclog">
import { onMounted } from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';

const { crudBinding, crudRef, crudExpose, resetCrudOptions } = useFs({
	createCrudOptions,
	context: {},
});

onMounted(() => {
	crudExpose.doRefresh();
});
</script>
