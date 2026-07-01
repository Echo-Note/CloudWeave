import * as api from './api';
import { dict, UserPageQuery, AddReq, DelReq, EditReq, compute, CreateCrudOptionsProps, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import { successMessage } from '/@/utils/message';
import { auth } from '/@/utils/authFunction';
import { useI18n } from 'vue-i18n';
import { commonCrudConfig } from '/@/utils/commonCrud';
import { shallowRef, h } from 'vue';
import { getBaseURL } from '/@/utils/baseUrl';
import OcrButton from './components/OcrButton';

export const createCrudOptions = function ({ crudExpose, context }: CreateCrudOptionsProps): CreateCrudOptionsRet {
  const { t } = useI18n();

  /**
   * 规范化表单数据中的 business_license 字段
   * 1. file-uploader 存数组 → 取第一个转字符串
   * 2. presigned URL（http 开头）→ 去掉域名和查询参数，还原为相对路径 media/{key}
   *    后端存储的是稳定的相对路径，presigned URL 会过期不能存
   * 3. pathname 中的 percent-encoding 需解码为原始字符，
   *    否则后端 default_storage.url() 会二次编码导致签名失效
   */
  const normalizeFormData = (form: Record<string, any>) => {
    let val = form.business_license;
    if (Array.isArray(val)) {
      val = val[0] || '';
    }
    if (typeof val === 'string' && val.startsWith('http')) {
      // presigned URL → 还原为相对路径（解码 percent-encoding）
      try {
        const urlObj = new URL(val);
        form.business_license = `media${decodeURIComponent(urlObj.pathname)}`;
      } catch {
        form.business_license = val;
      }
    } else {
      form.business_license = val;
    }
    return form;
  };

  const pageRequest = async (query: UserPageQuery) => await api.GetList(query);
  const editRequest = async ({ form, row }: EditReq) => {
    form.id = row.id;
    normalizeFormData(form);
    return await api.UpdateObj(form);
  };
  const delRequest = async ({ row }: DelReq) => await api.DelObj(row.id);
  const addRequest = async ({ form }: AddReq) => {
    normalizeFormData(form);
    return await api.AddObj(form);
  };

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
            show: auth('company:Create'),
            text: t('message.pages.company.buttons.add'),
          },
        },
      },
      // 行操作按钮
      rowHandle: {
        fixed: 'right',
        width: 280,
        buttons: {
          view: {
            show: true,
            text: t('message.pages.company.buttons.view'),
            iconRight: 'View',
            type: 'text',
          },
          edit: {
            text: t('message.pages.company.buttons.edit'),
            iconRight: 'Edit',
            type: 'text',
            show: auth('company:Update'),
          },
          remove: {
            text: t('message.pages.company.buttons.delete'),
            iconRight: 'Delete',
            type: 'text',
            show: auth('company:Delete'),
          },
          customToggleStatus: {
            text: compute((ctx: any) => {
              const { row } = ctx;
              return row.status === 'active'
                ? t('message.pages.company.buttons.deactivate')
                : t('message.pages.company.buttons.activate');
            }),
            type: 'text',
            show: auth('company:Update'),
            click: (ctx: any) => {
              const { row } = ctx;
              const newStatus = row.status === 'active' ? 'inactive' : 'active';
              api.BatchSetStatus([row.id], newStatus).then((res: any) => {
                successMessage(res.msg as string);
                crudExpose!.doRefresh();
              });
            },
          },
        },
      },
      // 表单弹窗配置
      form: {
        col: { span: 12 },
        labelWidth: '140px',
        wrapper: {
          is: 'el-dialog',
          width: '800px',
          onOpen: (ctx: any) => {
            (context as any).formSubmitted.value = false;
            (context as any).initialLicense.value = ctx.initialForm?.business_license || '';
            // 重置文件 ID，编辑已有记录时需要重新上传才能识别
            (context as any).licenseFileId.value = null;
          },
          onClosed: (ctx: any) => {
            if ((context as any).formSubmitted.value) return;
            const form = ctx.getFormData();
            const currentLicense = form?.business_license || '';
            const initialLicense = (context as any).initialLicense.value;
            if (currentLicense && currentLicense !== initialLicense) {
              api.DeleteUnusedFile(currentLicense).catch(() => {});
            }
          },
        },
        onSuccess: (ctx: any) => {
          (context as any).formSubmitted.value = true;
          return crudExpose!.doRefresh();
        },
      },
      // 列定义
      columns: {
        _index: {
          title: t('message.pages.company.table.columns.index'),
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
          title: t('message.pages.company.table.columns.name'),
          search: {
            show: true,
            col: { span: 8 },
            component: {
              props: { clearable: true },
              placeholder: t('message.pages.company.form.namePlaceholder'),
            },
          },
          type: 'input',
          column: {
            minWidth: 200,
          },
          form: {
            col: { span: 24 },
            rules: [
              { required: true, message: t('message.pages.company.validation.nameRequired') },
              { max: 200, message: t('message.pages.company.validation.nameMaxLength') },
            ],
            component: {
              props: { clearable: true },
              placeholder: t('message.pages.company.form.namePlaceholder'),
            },
          },
        },
        short_name: {
          title: t('message.pages.company.table.columns.shortName'),
          search: {
            show: true,
            col: { span: 8 },
            component: {
              props: { clearable: true },
              placeholder: t('message.pages.company.form.shortNamePlaceholder'),
            },
          },
          type: 'input',
          column: {
            minWidth: 120,
          },
          form: {
            col: { span: 12 },
            component: {
              props: { clearable: true, maxlength: 50 },
              placeholder: t('message.pages.company.form.shortNamePlaceholder'),
            },
          },
        },
        company_type: {
          title: t('message.pages.company.table.columns.companyType'),
          type: 'input',
          column: {
            minWidth: 160,
          },
          form: {
            col: { span: 12 },
            component: {
              props: { clearable: true, maxlength: 100 },
              placeholder: t('message.pages.company.form.companyTypePlaceholder'),
            },
          },
        },
        credit_code: {
          title: t('message.pages.company.table.columns.creditCode'),
          search: {
            show: true,
            col: { span: 8 },
            component: {
              props: { clearable: true },
              placeholder: t('message.pages.company.form.creditCodePlaceholder'),
            },
          },
          type: 'input',
          column: {
            minWidth: 180,
          },
          form: {
            col: { span: 12 },
            rules: [
              {
                pattern: /^[0-9A-Z]{18}$/,
                message: t('message.pages.company.validation.creditCodeFormat'),
                trigger: 'blur',
              },
            ],
            component: {
              props: { clearable: true, maxlength: 18 },
              placeholder: t('message.pages.company.form.creditCodePlaceholder'),
            },
          },
        },
        // ---- 工商信息 ----
        business_license: {
          title: t('message.pages.company.table.columns.businessLicense'),
          type: 'file-uploader',
          column: {
            minWidth: 120,
          },
          form: {
            col: { span: 24 },
            helper: t('message.pages.company.form.businessLicenseHelper'),
            component: {
              // 构建文件预览 URL（用于编辑模式回显已上传文件）
              buildUrl: async (value: any) => {
                if (!value) return '';
                // getBaseURL 自动处理 http URL（对象存储）和相对路径（本地）
                return getBaseURL(value);
              },
              // 上传成功后保存 file_id 到 context，供 OCR 按钮使用
              onSuccess: (ctx: any) => {
                // ctx = { res, file, fileList }
                // res 是 successHandle 返回值: { url, key: id, ...ret.data }
                const res = ctx?.res || {};
                const fileId = res.id || res.key;
                if (fileId) {
                  (context as any).licenseFileId.value = fileId;
                }
              },
            },
            bottomRender: (scope: any) => {
              const { form } = scope;
              const available = (context as any).ocrAvailable?.value;
              if (!available) {
                return null;
              }
              return h('div', { style: 'margin-top: 8px; text-align: right;' }, [
                h(OcrButton, {
                  getLicense: () => form.business_license,
                  getFileId: () => (context as any).licenseFileId?.value,
                  getForm: () => form,
                }),
              ]);
            }
          },
          viewForm: {
            col: { span: 24 },
            component: {
              name: 'fs-images-format',
              buildUrl: async (value: any) => {
                if (!value) return '';
                return getBaseURL(value);
              },
            },
          },
        },
        legal_person: {
          title: t('message.pages.company.table.columns.legalPerson'),
          type: 'input',
          column: {
            minWidth: 100,
          },
          form: {
            col: { span: 12 },
            component: {
              props: { clearable: true, maxlength: 50 },
              placeholder: t('message.pages.company.form.legalPersonPlaceholder'),
            },
          },
        },
        registered_capital: {
          title: t('message.pages.company.table.columns.registeredCapital'),
          type: 'number',
          column: {
            minWidth: 120,
            align: 'right',
          },
          form: {
            col: { span: 12 },
            component: {
              props: { precision: 2, step: 100, min: 0 },
              placeholder: t('message.pages.company.form.registeredCapitalPlaceholder'),
            },
          },
        },
        established_date: {
          title: t('message.pages.company.table.columns.establishedDate'),
          type: 'date',
          column: {
            minWidth: 120,
          },
          form: {
            col: { span: 12 },
            component: {
              props: { clearable: true, 'value-format': 'YYYY-MM-DD' },
              placeholder: t('message.pages.company.form.establishedDatePlaceholder'),
            },
          },
        },
        business_scope: {
          title: t('message.pages.company.table.columns.businessScope'),
          type: 'textarea',
          column: {
            minWidth: 200,
            'show-overflow-tooltip': true,
          },
          form: {
            col: { span: 24 },
            component: {
              props: { rows: 3, maxlength: 2000, 'show-word-limit': true },
              placeholder: t('message.pages.company.form.businessScopePlaceholder'),
            },
          },
        },
        address: {
          title: t('message.pages.company.table.columns.address'),
          type: 'textarea',
          column: {
            minWidth: 200,
            'show-overflow-tooltip': true,
          },
          form: {
            col: { span: 24 },
            component: {
              props: { rows: 2, maxlength: 500, 'show-word-limit': true },
              placeholder: t('message.pages.company.form.addressPlaceholder'),
            },
          },
        },
        // ---- 联系人信息 ----
        contact_person: {
          title: t('message.pages.company.table.columns.contactPerson'),
          type: 'input',
          column: {
            minWidth: 100,
          },
          form: {
            col: { span: 12 },
            component: {
              props: { clearable: true, maxlength: 50 },
              placeholder: t('message.pages.company.form.contactPersonPlaceholder'),
            },
          },
        },
        contact_phone: {
          title: t('message.pages.company.table.columns.contactPhone'),
          type: 'input',
          column: {
            minWidth: 130,
          },
          form: {
            col: { span: 12 },
            component: {
              props: { clearable: true, maxlength: 20 },
              placeholder: t('message.pages.company.form.contactPhonePlaceholder'),
            },
          },
        },
        contact_email: {
          title: t('message.pages.company.table.columns.contactEmail'),
          type: 'input',
          column: {
            minWidth: 180,
          },
          form: {
            col: { span: 12 },
            component: {
              props: { clearable: true },
              placeholder: t('message.pages.company.form.contactEmailPlaceholder'),
            },
          },
        },
        // ---- 层级 & 状态 ----
        parent: {
          title: t('message.pages.company.table.columns.parent'),
          type: 'dict-tree',
          column: {
            minWidth: 150,
            component: {
              name: 'fs-values-format',
              props: {
                multiple: false,
              },
            },
          },
          dict: dict({
            url: '/api/company/entity/parent_options/',
            value: 'id',
            label: 'name',
          }),
          form: {
            col: { span: 12 },
            component: {
              props: { clearable: true, 'check-strictly': true },
              placeholder: t('message.pages.company.form.parentPlaceholder'),
            },
            helper: t('message.pages.company.form.parentHelper'),
          },
        },
        status: {
          title: t('message.pages.company.table.columns.status'),
          search: { show: true },
          type: 'dict-radio',
          column: {
            minWidth: 90,
            component: {
              name: 'fs-dict-switch',
              activeText: '',
              inactiveText: '',
              style: '--el-switch-on-color: var(--el-color-primary); --el-switch-off-color: #dcdfe6',
              onChange: compute((context: any) => {
                return () => {
                  api.UpdateObj(context.row).then((res: any) => {
                    successMessage(res.msg as string);
                  });
                };
              }),
            },
          },
          dict: dict({
            data: [
              { value: 'active', label: t('message.pages.company.status.active') },
              { value: 'inactive', label: t('message.pages.company.status.inactive') },
            ],
          }),
          form: {
            col: { span: 12 },
            rules: [
              { required: true, message: t('message.pages.company.validation.statusRequired') },
            ],
            value: 'active',
          },
        },
        remark: {
          title: t('message.pages.company.table.columns.remark'),
          type: 'textarea',
          column: {
            minWidth: 150,
            'show-overflow-tooltip': true,
          },
          form: {
            col: { span: 24 },
            component: {
              props: { rows: 2, maxlength: 500, 'show-word-limit': true },
              placeholder: t('message.pages.company.form.remarkPlaceholder'),
            },
          },
        },
        // ---- 通用审计字段 ----
        ...commonFields,
      },
    },
  };
};
