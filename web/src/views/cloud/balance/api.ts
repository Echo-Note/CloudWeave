import { request } from '/@/utils/service';
import { PageQuery, InfoReq } from '@fast-crud/fast-crud';

/** 余额记录 API — 后端端点 /api/cloud/balance/（只读） */
export const apiPrefix = '/api/cloud/balance/';

/** 分页列表查询 */
export function GetList(query: PageQuery) {
	return request({ url: apiPrefix, method: 'get', params: query });
}

/** 单条详情 */
export function GetObj(id: InfoReq) {
	return request({ url: apiPrefix + id, method: 'get' });
}

/** 获取各云平台最新余额汇总 */
export function GetLatest() {
	return request({ url: apiPrefix + 'latest/', method: 'get' });
}
