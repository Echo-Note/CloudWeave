import { request } from '/@/utils/service';
import { PageQuery, AddReq, DelReq, EditReq, InfoReq } from '@fast-crud/fast-crud';

/** 云平台账号 API — 后端端点 /api/cloud/platform/ */
export const apiPrefix = '/api/cloud/platform/';

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

/** 批量删除 */
export function BatchDel(ids: number[]) {
	return request({ url: apiPrefix + 'multiple_delete/', method: 'delete', data: { keys: ids } });
}
