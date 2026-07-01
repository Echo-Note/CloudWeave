import { defineComponent, ref, h, PropType, nextTick } from 'vue';
import { ElButton } from 'element-plus';
import { MagicStick } from '@element-plus/icons-vue';
import { successMessage, warningMessage } from '/@/utils/message';
import { useI18n } from 'vue-i18n';
import * as api from '../api';

/**
 * OCR 营业执照识别按钮
 *
 * 通过文件 ID 发起 OCR 识别请求，识别成功后回填表单字段。
 * 文件 ID 由父组件在上传成功回调中记录。
 * 内部管理 loading 状态，防止重复点击。
 */
export default defineComponent({
  name: 'OcrButton',
  props: {
    /** 获取当前营业执照的文件 ID（上传成功时记录） */
    getFileId: {
      type: Function as PropType<() => number | string | null>,
      required: true,
    },
    /** 获取表单对象，用于回填识别结果 */
    getForm: {
      type: Function as PropType<() => Record<string, any>>,
      required: true,
    },
    /** 获取当前表单营业执照值（用于检查是否已上传） */
    getLicense: {
      type: Function as PropType<() => any>,
      required: true,
    },
  },
  setup(props) {
    const { t } = useI18n();
    const loading = ref(false);

    /** 将识别结果回填到表单 */
    const fillForm = (form: Record<string, any>, data: any) => {
      // 构建需要更新的字段映射（仅包含有值的字段）
      const updates: Record<string, any> = {};
      if (data.name) updates.name = data.name;
      if (data.short_name) updates.short_name = data.short_name;
      if (data.company_type) updates.company_type = data.company_type;
      if (data.credit_code) updates.credit_code = data.credit_code;
      if (data.legal_person) updates.legal_person = data.legal_person;
      if (data.registered_capital) {
        const num = parseFloat(data.registered_capital);
        if (!isNaN(num)) updates.registered_capital = num;
      }
      if (data.established_date) updates.established_date = data.established_date;
      if (data.business_scope) updates.business_scope = data.business_scope;
      if (data.address) updates.address = data.address;

      // 使用 Object.assign 批量赋值，确保 Vue 响应式系统能正确追踪变化
      Object.assign(form, updates);
    };

    const handleClick = async () => {
      if (loading.value) return;

      // 检查是否已上传文件
      const licenseValue = props.getLicense();
      if (!licenseValue) {
        warningMessage(t('message.pages.company.messages.uploadLicenseFirst') as string);
        return;
      }

      const fileId = props.getFileId();
      if (!fileId) {
        warningMessage(t('message.pages.company.messages.uploadLicenseFirst') as string);
        return;
      }

      loading.value = true;
      try {
        const res: any = await api.RecognizeLicense(fileId);
        const data = res.data || {};
        const form = props.getForm();
        fillForm(form, data);
        // 等待 Vue 响应式更新完成，确保 FastCrud 表单状态同步
        await nextTick();
        successMessage(t('message.pages.company.messages.ocrRecognizeSuccess') as string);
      } catch {
        warningMessage(t('message.pages.company.messages.ocrRecognizeFailed') as string);
      } finally {
        loading.value = false;
      }
    };

    return () =>
      h(ElButton, {
        type: 'success',
        plain: true,
        size: 'small',
        icon: MagicStick,
        nativeType: 'button',
        loading: loading.value,
        disabled: loading.value,
        onClick: handleClick,
      }, () => loading.value
        ? t('message.pages.company.messages.ocrRecognizing') as string || '识别中...'
        : t('message.pages.company.buttons.aiRecognize'));
  },
});

