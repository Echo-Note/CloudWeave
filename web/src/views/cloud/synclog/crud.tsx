import * as api from './api';
import { dict, UserPageQuery, CreateCrudOptionsProps, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import { auth } from '/@/utils/authFunction';

export const createCrudOptions = function ({ crudExpose }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	const pageRequest = async (query: UserPageQuery) => await api.GetList(query);

	return {
		crudOptions: {
			request: { pageRequest },
			// 只读列表：隐藏新增按钮
			actionbar: { show: true, buttons: { add: { show: false } } },
			// 只读列表：隐藏行操作按钮，仅保留查看
			rowHandle: {
				fixed: 'right',
				width: 100,
				buttons: {
					edit: { show: false },
					remove: { show: false },
					view: {
						show: auth('cloud_synclog:Query'),
						text: '查看',
						iconRight: 'View',
						type: 'text',
					},
				},
			},
			// 表单弹窗配置（仅查看用）
			form: {
				col: { span: 12 },
				labelWidth: '130px',
				wrapper: {
					is: 'el-dialog',
					width: '700px',
				},
			},
			// 列定义
			columns: {
				_index: {
					title: '序号',
					form: { show: false },
					column: {
						align: 'center',
						width: '60px',
						columnSetDisabled: true,
						formatter: (context: any) => {
							const index = context.index ?? 1;
							const pagination = crudExpose!.crudBinding.value.pagination;
							return ((pagination!.currentPage ?? 1) - 1) * pagination!.pageSize + index + 1;
						},
					},
				},
				cloud_platform_name: {
					title: '云平台',
					search: {
						show: true,
						col: { span: 8 },
						component: { props: { clearable: true }, placeholder: '请输入云平台名称' },
					},
					type: 'input',
					column: { minWidth: 140 },
					form: { show: false },
				},
				sync_type: {
					title: '同步类型',
					search: { show: true },
					type: 'dict-select',
					column: { minWidth: 100 },
					dict: dict({
						data: [
							{ value: 'full', label: '全量同步' },
							{ value: 'incremental', label: '增量同步' },
						],
					}),
					form: { show: false },
				},
				trigger: {
					title: '触发方式',
					search: { show: true },
					type: 'dict-select',
					column: { minWidth: 100 },
					dict: dict({
						data: [
							{ value: 'manual', label: '手动触发' },
							{ value: 'scheduled', label: '定时触发' },
						],
					}),
					form: { show: false },
				},
				status: {
					title: '同步状态',
					search: { show: true },
					type: 'dict-select',
					column: { minWidth: 100 },
					dict: dict({
						data: [
							{ value: 'running', label: '进行中', color: 'primary' },
							{ value: 'success', label: '成功', color: 'success' },
							{ value: 'failed', label: '失败', color: 'danger' },
							{ value: 'partial', label: '部分成功', color: 'warning' },
						],
					}),
					form: { show: false },
				},
				assets_created: {
					title: '新增资产',
					type: 'number',
					column: { minWidth: 90, align: 'center' },
					form: { show: false },
				},
				assets_updated: {
					title: '更新资产',
					type: 'number',
					column: { minWidth: 90, align: 'center' },
					form: { show: false },
				},
				assets_terminated: {
					title: '下线资产',
					type: 'number',
					column: { minWidth: 90, align: 'center' },
					form: { show: false },
				},
				error_detail: {
					title: '错误详情',
					type: 'textarea',
					column: { minWidth: 200, 'show-overflow-tooltip': true },
					form: {
						col: { span: 24 },
						component: { props: { rows: 4, readonly: true } },
					},
				},
				started_at: {
					title: '开始时间',
					type: 'datetime',
					column: { minWidth: 160 },
					form: { show: false },
				},
				finished_at: {
					title: '结束时间',
					type: 'datetime',
					column: { minWidth: 160 },
					form: { show: false },
				},
				create_datetime: {
					title: '创建时间',
					type: 'datetime',
					column: { minWidth: 160 },
					form: { show: false },
				},
			},
		},
	};
};
