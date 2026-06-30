"""
告警管理 — 数据模型

支持余额阈值、资源到期、同步失败三类告警规则配置，
告警记录追踪（触发→确认→解决）及通知收敛。
"""
from django.conf import settings
from django.db import models

from dvadmin.utils.models import CoreModel, table_prefix


class AlertRule(CoreModel):
    """
    告警规则表

    定义告警的触发条件、级别、通知渠道和收敛策略。
    支持独立启用/停用，免打扰时段配置。
    """
    name = models.CharField(
        max_length=200,
        verbose_name="规则名称", help_text="告警规则名称",
        db_comment="规则名称"
    )
    alert_type = models.CharField(
        max_length=30,
        choices=(
            ('balance_threshold', '余额阈值'),
            ('resource_expire', '资源到期'),
            ('sync_failure', '同步失败'),
        ),
        verbose_name="告警类型", help_text="告警类型",
        db_comment="告警类型"
    )
    cloud_platform = models.ForeignKey(
        'cloud.CloudPlatform', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="告警目标云账号", help_text="告警目标云账号（为空表示所有账号）",
        db_comment="告警目标云账号"
    )
    severity = models.CharField(
        max_length=20, default='warning',
        choices=(
            ('critical', '严重'),
            ('warning', '警告'),
            ('info', '提醒'),
        ),
        verbose_name="告警级别", help_text="告警级别：critical(严重)/warning(警告)/info(提醒)",
        db_comment="告警级别"
    )
    condition_config = models.JSONField(
        verbose_name="触发条件",
        help_text=(
            "触发条件JSON。余额阈值: {'threshold': 1000, 'operator': 'lte'}；"
            "资源到期: {'days_before': [30, 15, 7], 'resource_types': ['server','domain']}；"
            "同步失败: {'consecutive_failures': 3}"
        ),
        db_comment="触发条件"
    )
    cooldown_minutes = models.IntegerField(
        default=120,
        verbose_name="冷却时间(分钟)", help_text="通知冷却时间，默认120分钟，期间不重复通知",
        db_comment="冷却时间(分钟)"
    )
    channels = models.JSONField(
        verbose_name="通知渠道",
        help_text="通知渠道JSON数组，可选值：in_app / email / wecom",
        db_comment="通知渠道"
    )
    quiet_start = models.TimeField(
        null=True, blank=True,
        verbose_name="免打扰开始", help_text="免打扰开始时间，如22:00",
        db_comment="免打扰开始"
    )
    quiet_end = models.TimeField(
        null=True, blank=True,
        verbose_name="免打扰结束", help_text="免打扰结束时间，如08:00",
        db_comment="免打扰结束"
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name="是否启用", help_text="是否启用该告警规则",
        db_comment="是否启用"
    )

    class Meta:
        db_table = f"{table_prefix}alert_rule"
        verbose_name = "告警规则"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return f"{self.name} [{self.get_severity_display()}]"


class AlertRuleUsers(CoreModel):
    """
    告警通知人关联表

    告警规则与通知对象的多对多关联。
    """
    alert_rule = models.ForeignKey(
        AlertRule, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="告警规则", help_text="告警规则",
        db_comment="告警规则"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        db_constraint=False, related_name='alert_rule_users_set',
        verbose_name="通知对象", help_text="接收告警通知的用户",
        db_comment="通知对象"
    )

    class Meta:
        db_table = f"{table_prefix}alert_rule_users"
        verbose_name = "告警通知人"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['alert_rule', 'user'],
                name='uq_alert_rule_user'
            ),
        ]

    def __str__(self):
        return f"{self.alert_rule} → {self.user}"


class AlertRecord(CoreModel):
    """
    告警记录表

    记录每次告警触发的详情，包含确认/解决状态和处理备注。
    """
    alert_rule = models.ForeignKey(
        AlertRule, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联告警规则", help_text="关联告警规则",
        db_comment="关联告警规则"
    )
    alert_type = models.CharField(
        max_length=30,
        verbose_name="告警类型", help_text="告警类型（冗余存储，方便查询）",
        db_comment="告警类型"
    )
    severity = models.CharField(
        max_length=20,
        verbose_name="告警级别", help_text="critical / warning / info",
        db_comment="告警级别"
    )
    title = models.CharField(
        max_length=300,
        verbose_name="告警标题", help_text="告警标题，如'腾讯云账号xxx余额不足100元'",
        db_comment="告警标题"
    )
    message = models.TextField(
        verbose_name="告警详情", help_text="告警详情描述",
        db_comment="告警详情"
    )
    cloud_platform = models.ForeignKey(
        'cloud.CloudPlatform', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="关联云账号", help_text="关联云账号",
        db_comment="关联云账号"
    )
    related_resource_type = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="关联资源类型",
        help_text="关联资源类型：server / domain / cloud_platform",
        db_comment="关联资源类型"
    )
    related_resource_id = models.BigIntegerField(
        null=True, blank=True,
        verbose_name="关联资源ID", help_text="关联资源ID",
        db_comment="关联资源ID"
    )
    current_value = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name="触发时实际值", help_text="触发时的实际值，如'余额: 85.50元'",
        db_comment="触发时实际值"
    )
    status = models.CharField(
        max_length=20, default='triggered',
        choices=(
            ('triggered', '已触发'),
            ('acknowledged', '已确认'),
            ('resolved', '已解决'),
        ),
        verbose_name="状态", help_text="告警处理状态",
        db_comment="状态"
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alerts_acknowledged', db_constraint=False,
        verbose_name="确认人", help_text="确认人",
        db_comment="确认人"
    )
    acknowledged_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="确认时间", help_text="确认时间",
        db_comment="确认时间"
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alerts_resolved', db_constraint=False,
        verbose_name="解决人", help_text="解决人",
        db_comment="解决人"
    )
    resolved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="解决时间", help_text="解决时间",
        db_comment="解决时间"
    )
    resolve_note = models.TextField(
        null=True, blank=True,
        verbose_name="处理备注", help_text="处理备注",
        db_comment="处理备注"
    )
    triggered_at = models.DateTimeField(
        verbose_name="触发时间", help_text="告警触发时间",
        db_comment="触发时间"
    )

    class Meta:
        db_table = f"{table_prefix}alert_record"
        verbose_name = "告警记录"
        verbose_name_plural = verbose_name
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['alert_type', 'status'], name='idx_alert_type_status'),
            models.Index(fields=['triggered_at'], name='idx_alert_triggered_at'),
        ]

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"
