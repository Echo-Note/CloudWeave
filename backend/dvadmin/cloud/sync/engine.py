"""
云平台同步 — 同步引擎

职责：
  1. 根据云平台名称选择对应的同步器（工厂模式）
  2. 执行同步流程
  3. 写入 SyncLog 同步日志
  4. 更新 CloudPlatform 的 last_sync_at / last_sync_status

使用方式：
    from dvadmin.cloud.sync.engine import SyncEngine

    engine = SyncEngine(cloud_platform)
    engine.run(trigger="manual", sync_type="full")
"""
import logging
from typing import Optional

from django.utils import timezone

from dvadmin.cloud.models import CloudPlatform, SyncLog
from dvadmin.cloud.sync.aliyun import AliyunSyncer
from dvadmin.cloud.sync.base import BaseCloudSyncer
from dvadmin.cloud.sync.huawei import HuaweiCloudSyncer
from dvadmin.cloud.sync.meicheng import MeichengSyncer
from dvadmin.cloud.sync.schemas import SyncResult
from dvadmin.cloud.sync.tencent import TencentCloudSyncer

logger = logging.getLogger(__name__)

# 平台名称 → 同步器类 的映射（工厂注册表）
SYNCER_REGISTRY: dict[str, type[BaseCloudSyncer]] = {
    # 腾讯云
    "腾讯云": TencentCloudSyncer,
    "tencent": TencentCloudSyncer,
    "tencentcloud": TencentCloudSyncer,
    # 阿里云
    "阿里云": AliyunSyncer,
    "aliyun": AliyunSyncer,
    "alibaba": AliyunSyncer,
    "alibabacloud": AliyunSyncer,
    # 华为云
    "华为云": HuaweiCloudSyncer,
    "huawei": HuaweiCloudSyncer,
    "huaweicloud": HuaweiCloudSyncer,
    # 美橙
    "美橙": MeichengSyncer,
    "美橙互联": MeichengSyncer,
    "meicheng": MeichengSyncer,
}


def get_syncer(cloud_platform: CloudPlatform) -> Optional[BaseCloudSyncer]:
    """
    工厂方法：根据云平台名称获取对应的同步器实例

    :param cloud_platform: 云平台账号
    :return: 同步器实例，未匹配返回 None
    """
    name = cloud_platform.name.strip().lower()
    syncer_cls = SYNCER_REGISTRY.get(name)
    if syncer_cls is None:
        # 模糊匹配
        for key, cls in SYNCER_REGISTRY.items():
            if key in name:
                syncer_cls = cls
                break
    if syncer_cls is None:
        return None
    return syncer_cls(cloud_platform)


class SyncEngine:
    """
    同步引擎

    封装完整的同步流程：创建日志 → 执行同步 → 汇总结果 → 更新状态。
    """

    def __init__(self, cloud_platform: CloudPlatform):
        self.cloud_platform = cloud_platform
        self.syncer = get_syncer(cloud_platform)

    def run(
        self,
        trigger: str = "manual",
        sync_type: str = "full",
        resources: Optional[list[str]] = None,
    ) -> SyncLog:
        """
        执行同步

        :param trigger: 触发方式 manual / scheduled
        :param sync_type: 同步类型 full / incremental
        :param resources: 指定同步资源列表，为空则同步厂商支持的全部资源
        :return: SyncLog 日志记录
        """
        # 创建同步日志
        log = SyncLog.objects.create(
            cloud_platform=self.cloud_platform,
            sync_type=sync_type,
            trigger=trigger,
            status="running",
            started_at=timezone.now(),
        )

        if self.syncer is None:
            log.status = "failed"
            log.error_detail = [{"item": "syncer", "error": f"不支持的平台: {self.cloud_platform.name}"}]
            log.finished_at = timezone.now()
            log.save()
            self._update_platform_status("failed")
            return log

        try:
            # 执行同步
            results = self.syncer.sync_all(resources=resources)

            # 汇总
            total_created = sum(r.created for r in results.values())
            total_updated = sum(r.updated for r in results.values())
            total_terminated = sum(r.terminated for r in results.values())
            all_errors = []
            for r in results.values():
                all_errors.extend(r.errors)

            # 判断最终状态
            if not all_errors:
                status = "success"
            elif total_created + total_updated > 0:
                status = "partial"
            else:
                status = "failed"

            log.status = status
            log.assets_created = total_created
            log.assets_updated = total_updated
            log.assets_terminated = total_terminated
            log.error_detail = all_errors if all_errors else None
            log.finished_at = timezone.now()
            log.save()

            self._update_platform_status(status)
            logger.info(
                "云平台 %s 同步完成: 新增=%d 更新=%d 下线=%d 错误=%d 状态=%s",
                self.cloud_platform.name,
                total_created,
                total_updated,
                total_terminated,
                len(all_errors),
                status,
            )
            return log

        except Exception as e:
            log.status = "failed"
            log.error_detail = [{"item": "engine", "error": str(e)}]
            log.finished_at = timezone.now()
            log.save()
            self._update_platform_status("failed")
            logger.exception("云平台 %s 同步异常", self.cloud_platform.name)
            return log

    def _update_platform_status(self, status: str) -> None:
        """更新云平台账号的最近同步状态"""
        self.cloud_platform.last_sync_at = timezone.now()
        self.cloud_platform.last_sync_status = status
        self.cloud_platform.save(update_fields=["last_sync_at", "last_sync_status"])
