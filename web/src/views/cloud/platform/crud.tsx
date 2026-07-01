import * as api from './api';
import { dict, UserPageQuery, AddReq, DelReq, EditReq, CreateCrudOptionsProps, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import { successMessage } from '/@/utils/message';
import { auth } from '/@/utils/authFunction';
import { commonCrudConfig } from '/@/utils/commonCrud';

export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
	const pageRequest = async (query: UserPageQuery) => await api.GetList(query);
	const editRequest = async ({ form, row }: EditReq) => {
		form.id = row.id;
		return await api.UpdateObj(form);
	};
	const delRequest = async ({ row }: DelReq) => await api.DelObj(row.id);
	const addRequest = async ({ form }: AddReq) => await api.AddObj(form);

	// 引入通用字段（创建时间、更新时间、创建人、修改人、部门、备注）
	const commonFields = commonCrudConfig({
		create_datetime: { table: true, search: false },
		update_datetime: { table: true, search: false },
		creator_name: { table: true },
		modifier_name: { table: true },
		description: { table: false },
		dept_belong_id: { table: false, form: false, search: false },
	});

	return {
		crudOptions: {
			request: { pageRequest, addRequest, editRequest, delRequest },
			// 顶部操作栏
			actionbar: {
				buttons: {
					add: {
						show: auth('cloud_platform:Create'),
						text: '新增账号',
					},
				},
			},
			// 行操作按钮
			rowHandle: {
				fixed: 'right',
				width: 200,
				buttons: {
					view: {
						show: true,
						text: '查看',
						iconRight: 'View',
						type: 'text',
					},
					edit: {
						text: '编辑',
						iconRight: 'Edit',
						type: 'text',
						show: auth('cloud_platform:Update'),
					},
					remove: {
						text: '删除',
						iconRight: 'Delete',
						type: 'text',
						show: auth('cloud_platform:Delete'),
					},
				},
			},
			// 表单弹窗配置
			form: {
				col: { span: 12 },
				labelWidth: '130px',
				wrapper: {
					is: 'el-dialog',
					width: '800px',
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
				// ---- 核心字段 ----
				name: {
					title: '平台名称',
					search: {
						show: true,
						col: { span: 8 },
						component: { props: { clearable: true }, placeholder: '请输入平台名称' },
					},
					type: 'input',
					column: { minWidth: 140 },
					form: {
						col: { span: 12 },
						rules: [{ required: true, message: '请输入平台名称' }],
						component: { props: { clearable: true }, placeholder: '腾讯云/阿里云/华为云/AWS等' },
					},
				},
				account_alias: {
					title: '账号别名',
					search: {
						show: true,
						col: { span: 8 },
						component: { props: { clearable: true }, placeholder: '请输入账号别名' },
					},
					type: 'input',
					column: { minWidth: 120 },
					form: {
						col: { span: 12 },
						component: { props: { clearable: true, maxlength: 100 }, placeholder: '便于内部识别的别名' },
					},
				},
				account_id: {
					title: '账号ID/UIN',
					type: 'input',
					column: { minWidth: 140 },
					form: {
						col: { span: 12 },
						component: { props: { clearable: true }, placeholder: '云平台账号ID或UIN' },
					},
				},
				company: {
					title: '归属公司',
					type: 'dict-select',
					column: { minWidth: 140 },
					form: {
						col: { span: 12 },
						component: { props: { clearable: true }, placeholder: '选择费用归属公司' },
					},
					dict: dict({
						url: '/api/company/entity/parent_options/',
						value: 'id',
						label: 'name',
					}),
				},
				contact_person: {
					title: '联系人',
					type: 'input',
					column: { minWidth: 100 },
					form: {
						col: { span: 12 },
						component: { props: { clearable: true, maxlength: 50 }, placeholder: '联系人姓名' },
					},
				},
				// ---- API 凭证 ----
				secret_id: {
					title: 'SecretId',
					type: 'input',
					column: { show: false },
					form: {
						col: { span: 12 },
						component: { props: { clearable: true }, placeholder: 'API SecretId（加密存储）' },
					},
				},
				secret_key: {
					title: 'SecretKey',
					type: 'input',
					column: { show: false },
					form: {
						col: { span: 12 },
						component: { props: { clearable: true, showPassword: true }, placeholder: 'API SecretKey（加密存储）' },
					},
				},
				// ---- 同步配置 ----
				sync_enabled: {
					title: '启用同步',
					search: { show: true },
					type: 'dict-switch',
					column: {
						minWidth: 100,
						component: {
							name: 'fs-dict-switch',
							activeText: '',
							inactiveText: '',
							style: '--el-switch-on-color: var(--el-color-primary); --el-switch-off-color: #dcdfe6',
						},
					},
					dict: dict({
						data: [
							{ value: true, label: '启用' },
							{ value: false, label: '禁用' },
						],
					}),
					form: {
						col: { span: 12 },
						value: false,
					},
				},
				sync_regions: {
					title: '同步地域',
					type: 'textarea',
					column: { show: false },
					form: {
						col: { span: 24 },
						helper: 'JSON 数组格式，如：["ap-guangzhou","ap-shanghai"]',
						component: { props: { rows: 2 }, placeholder: '同步地域列表JSON' },
					},
				},
				sync_services: {
					title: '同步服务',
					type: 'textarea',
					column: { show: false },
					form: {
						col: { span: 24 },
						helper: 'JSON 数组格式，如：["cvm","billing"]',
						component: { props: { rows: 2 }, placeholder: '同步服务列表JSON' },
					},
				},
				sync_interval_minutes: {
					title: '同步间隔(分钟)',
					type: 'number',
					column: { minWidth: 130 },
					form: {
						col: { span: 12 },
						component: { props: { min: 1, step: 30 }, placeholder: '默认360分钟' },
					},
				},
				last_sync_at: {
					title: '最近同步时间',
					type: 'datetime',
					column: { minWidth: 160 },
					form: { show: false },
				},
				last_sync_status: {
					title: '最近同步状态',
					search: { show: true },
					type: 'dict-select',
					column: { minWidth: 120 },
					dict: dict({
						data: [
							{ value: 'success', label: '成功', color: 'success' },
							{ value: 'failed', label: '失败', color: 'danger' },
							{ value: 'partial', label: '部分成功', color: 'warning' },
						],
					}),
					form: { show: false },
				},
				remark: {
					title: '备注',
					type: 'textarea',
					column: { minWidth: 150, 'show-overflow-tooltip': true },
					form: {
						col: { span: 24 },
						component: { props: { rows: 2, maxlength: 500, 'show-word-limit': true }, placeholder: '请输入备注' },
					},
				},
				// ---- 通用审计字段 ----
				...commonFields,
			},
		},
	};
};
