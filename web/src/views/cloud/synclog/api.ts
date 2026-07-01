import { request } from '/@/utils/service';
import { PageQuery, InfoReq } from '@fast-crud/fast-crud';

/** 同步日志 API — 后端端点 /api/cloud/sync_log/（只读） */
export const apiPrefix = '/api/cloud/sync_log/';

/** 分页列表查询 */
export function GetList(query: PageQuery) {
	return request({ url: apiPrefix, method: 'get', params: query });
}

/** 单条详情 */
export function GetObj(id: InfoReq) {
	return request({ url: apiPrefix + id, method: 'get' });
}
