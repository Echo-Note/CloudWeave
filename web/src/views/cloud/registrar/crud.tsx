import * as api from './api';
import { dict, UserPageQuery, AddReq, DelReq, EditReq, CreateCrudOptionsProps, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import { auth } from '/@/utils/authFunction';
import { commonCrudConfig } from '/@/utils/commonCrud';

export const createCrudOptions = function ({ crudExpose }: CreateCrudOptionsProps): CreateCrudOptionsRet {
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
						show: auth('cloud_registrar:Create'),
						text: '新增注册商',
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
						show: auth('cloud_registrar:Update'),
					},
					remove: {
						text: '删除',
						iconRight: 'Delete',
						type: 'text',
						show: auth('cloud_registrar:Delete'),
					},
				},
			},
			// 表单弹窗配置
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
				name: {
					title: '注册商名称',
					search: {
						show: true,
						col: { span: 8 },
						component: { props: { clearable: true }, placeholder: '请输入注册商名称' },
					},
					type: 'input',
					column: { minWidth: 140 },
					form: {
						col: { span: 12 },
						rules: [{ required: true, message: '请输入注册商名称' }],
						component: { props: { clearable: true }, placeholder: '腾讯云/阿里云/美橙/易名/GoDaddy等' },
					},
				},
				account_alias: {
					title: '注册账户别名',
					search: {
						show: true,
						col: { span: 8 },
						component: { props: { clearable: true }, placeholder: '请输入账户别名' },
					},
					type: 'input',
					column: { minWidth: 140 },
					form: {
						col: { span: 12 },
						component: { props: { clearable: true, maxlength: 100 }, placeholder: '注册账户别名' },
					},
				},
			account_id: {
				title: '注册账户ID',
				type: 'input',
				column: { minWidth: 140 },
				form: {
					col: { span: 12 },
					component: { props: { clearable: true }, placeholder: '注册账户ID' },
				},
			},
			cloud_platform: {
				title: '关联云平台',
				type: 'dict-select',
				column: { minWidth: 140 },
				form: {
					col: { span: 12 },
					helper: '云厂商注册商复用云平台账号密钥，独立注册商留空',
					component: { props: { clearable: true }, placeholder: '选择关联云平台账号' },
				},
				dict: dict({
					url: '/api/cloud/platform/',
					value: 'id',
					label: 'name',
				}),
			},
			company: {
					title: '归属公司',
					type: 'dict-select',
					column: { minWidth: 140 },
					form: {
						col: { span: 12 },
						component: { props: { clearable: true }, placeholder: '选择归属公司' },
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
