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
						show: auth('cloud_balance:Query'),
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
					width: '600px',
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
				cash_balance: {
					title: '现金余额',
					type: 'number',
					column: { minWidth: 120, align: 'right' },
					form: { component: { props: { readonly: true } } },
				},
				voucher_balance: {
					title: '代金券余额',
					type: 'number',
					column: { minWidth: 120, align: 'right' },
					form: { component: { props: { readonly: true } } },
				},
				credit_balance: {
					title: '信用额度',
					type: 'number',
					column: { minWidth: 120, align: 'right' },
					form: { component: { props: { readonly: true } } },
				},
				frozen_amount: {
					title: '冻结金额',
					type: 'number',
					column: { minWidth: 120, align: 'right' },
					form: { component: { props: { readonly: true } } },
				},
				total_balance: {
					title: '总可用余额',
					type: 'number',
					column: { minWidth: 130, align: 'right' },
					form: { component: { props: { readonly: true } } },
				},
				currency: {
					title: '币种',
					search: { show: true },
					type: 'dict-select',
					column: { minWidth: 80, align: 'center' },
					dict: dict({
						data: [
							{ value: 'CNY', label: 'CNY' },
							{ value: 'USD', label: 'USD' },
						],
					}),
					form: { show: false },
				},
				recorded_at: {
					title: '记录时间',
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
