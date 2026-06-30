"""
ICP 备案管理 — 数据模型

域名 ICP 备案信息的登记、变更审核与历史追溯。
"""
from django.conf import settings
from django.db import models

from dvadmin.utils.models import CoreModel, table_prefix


class IcpRecord(CoreModel):
    """
    备案记录表

    与域名一对一关联，记录 ICP 备案号、主体信息、负责人等。
    """
    domain = models.OneToOneField(
        'assets.Domain', on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联域名", help_text="关联域名（一对一）",
        db_comment="关联域名"
    )
    icp_number = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="备案号", help_text="备案号，如'京ICP备2024XXXXXX号'",
        db_comment="备案号"
    )
    company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.PROTECT,
        db_constraint=False,
        verbose_name="备案主体公司", help_text="备案主体公司（FK关联统一主体表）",
        db_comment="备案主体公司"
    )
    company_type = models.CharField(
        max_length=20, default='enterprise',
        choices=(
            ('enterprise', '企业'),
            ('individual', '个人'),
            ('government', '政府机关'),
            ('other', '其他'),
        ),
        verbose_name="单位性质", help_text="单位性质",
        db_comment="单位性质"
    )
    contact_person = models.CharField(
        max_length=50,
        verbose_name="负责人姓名", help_text="负责人姓名",
        db_comment="负责人姓名"
    )
    contact_phone = models.CharField(
        max_length=20,
        verbose_name="负责人联系电话", help_text="负责人联系电话",
        db_comment="负责人联系电话"
    )
    contact_email = models.EmailField(
        null=True, blank=True,
        verbose_name="负责人邮箱", help_text="负责人邮箱",
        db_comment="负责人邮箱"
    )
    approval_date = models.DateField(
        null=True, blank=True,
        verbose_name="审核通过日期", help_text="备案审核通过日期",
        db_comment="审核通过日期"
    )
    review_remind_date = models.DateField(
        null=True, blank=True,
        verbose_name="复核提醒日期", help_text="备案复核提醒日期",
        db_comment="复核提醒日期"
    )
    status = models.CharField(
        max_length=20, default='active',
        choices=(('active', '生效中'), ('changed', '已变更')),
        verbose_name="记录状态", help_text="备案记录状态",
        db_comment="记录状态"
    )

    class Meta:
        db_table = f"{table_prefix}icp_record"
        verbose_name = "ICP备案记录"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        domain_name = self.domain.name if self.domain else '-'
        return f"{domain_name} - {self.icp_number or '未备案'}"


class IcpChangeLog(CoreModel):
    """
    备案变更历史表

    记录每次备案信息变更的 Before/After 快照，含审核状态。
    变更审核状态机：draft → pending → approved / rejected → pending (重新提交)
    """
    icp_record = models.ForeignKey(
        IcpRecord, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联备案记录", help_text="关联备案记录",
        db_comment="关联备案记录"
    )
    field_name = models.CharField(
        max_length=50,
        verbose_name="变更字段名", help_text="变更字段名，如contact_person/contact_phone",
        db_comment="变更字段名"
    )
    old_value = models.TextField(
        null=True, blank=True,
        verbose_name="变更前值", help_text="变更前值",
        db_comment="变更前值"
    )
    new_value = models.TextField(
        verbose_name="变更后值", help_text="变更后值",
        db_comment="变更后值"
    )
    change_reason = models.TextField(
        null=True, blank=True,
        verbose_name="变更原因", help_text="变更原因说明",
        db_comment="变更原因"
    )
    status = models.CharField(
        max_length=20, default='draft',
        choices=(
            ('draft', '草稿'),
            ('pending', '待审核'),
            ('approved', '已通过'),
            ('rejected', '已驳回'),
        ),
        verbose_name="审核状态", help_text="审核状态",
        db_comment="审核状态"
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='icp_changes_submitted', db_constraint=False,
        verbose_name="提交人", help_text="变更提交人",
        db_comment="提交人"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='icp_changes_reviewed', db_constraint=False,
        verbose_name="审核人", help_text="审核人",
        db_comment="审核人"
    )
    reviewed_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="审核时间", help_text="审核时间",
        db_comment="审核时间"
    )

    class Meta:
        db_table = f"{table_prefix}icp_change_log"
        verbose_name = "备案变更历史"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return f"{self.icp_record} - {self.field_name}: {self.old_value} → {self.new_value}"
