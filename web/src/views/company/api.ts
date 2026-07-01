import { request } from '/@/utils/service';
import { PageQuery, AddReq, DelReq, EditReq, InfoReq } from '@fast-crud/fast-crud';

/** 主体公司 API — 后端端点 /api/company/entity/ */
export const apiPrefix = '/api/company/entity/';

/** 分页列表查询 */
export function GetList(query: PageQuery) {
    return request({ url: apiPrefix, method: 'get', params: query });
}

/** 单条详情 */
export function GetObj(id: InfoReq) {
    return request({ url: apiPrefix + id, method: 'get' });
}

/** 新增 */
export function AddObj(obj: AddReq) {
    return request({ url: apiPrefix, method: 'post', data: obj });
}

/** 修改 */
export function UpdateObj(obj: EditReq) {
    return request({ url: apiPrefix + obj.id + '/', method: 'put', data: obj });
}

/** 删除 */
export function DelObj(id: DelReq) {
    return request({ url: apiPrefix + id + '/', method: 'delete', data: { id } });
}

/** 获取上级主体下拉选项（用于表单中选择上级） */
export function GetParentOptions(excludeId?: number) {
    const params: any = {};
    if (excludeId) params.exclude_id = excludeId;
    return request({ url: apiPrefix + 'parent_options/', method: 'get', params });
}

/** 批量设置状态 */
export function BatchSetStatus(ids: number[], status: string) {
    return request({
        url: apiPrefix + 'batch_set_status/',
        method: 'post',
        data: { ids, status },
    });
}

/** 检查 OCR 引擎是否可用 */
export function CheckOcrStatus() {
    return request({ url: apiPrefix + 'ocr_status/', method: 'get' });
}

/** OCR 营业执照识别 — 传入文件 ID，返回识别结果 */
export function RecognizeLicense(fileId: number | string) {
    return request({
        url: apiPrefix + 'recognize_license/',
        method: 'post',
        data: { file_id: fileId },
        timeout: 60000, // OCR 首次加载模型 + 识别耗时较长，60s 超时
    });
}

/** 删除未使用的上传文件 */
export function DeleteUnusedFile(url: string) {
    return request({
        url: '/api/system/file/delete_by_url/',
        method: 'post',
        data: { url },
    });
}
