"""
云平台管理 — 数据模型

统一管理企业使用的云平台账号、域名注册商信息，
以及 API 同步日志和账户余额记录。
"""
from django.db import models

from dvadmin.utils.models import CoreModel, table_prefix


class CloudPlatform(CoreModel):
    """
    云平台账号表

    统一管理各云平台账号及其 API 凭证（加密存储），
    支持多地域、多服务的同步配置。
    """
    name = models.CharField(
        max_length=100,
        verbose_name="平台名称", help_text="云平台名称：腾讯云/阿里云/华为云/AWS/Azure/私有化",
        db_comment="平台名称"
    )
    account_alias = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="账号别名", help_text="账号别名，便于内部识别",
        db_comment="账号别名"
    )
    account_id = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name="账号ID/UIN", help_text="云平台账号ID或UIN",
        db_comment="账号ID/UIN"
    )
    company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="归属主体公司", help_text="费用归属主体公司",
        db_comment="归属主体公司"
    )
    contact_person = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="联系人", help_text="联系人姓名",
        db_comment="联系人"
    )
    # API 凭证（AES-256 加密存储）
    secret_id = models.CharField(
        max_length=500, null=True, blank=True,
        verbose_name="SecretId", help_text="API SecretId / AccessKeyId（加密存储）",
        db_comment="SecretId"
    )
    secret_key = models.CharField(
        max_length=1000, null=True, blank=True,
        verbose_name="SecretKey", help_text="API SecretKey / AccessKeySecret（加密存储）",
        db_comment="SecretKey"
    )
    # 同步配置
    sync_enabled = models.BooleanField(
        default=False,
        verbose_name="启用API同步", help_text="是否启用API自动同步",
        db_comment="启用API同步"
    )
    sync_regions = models.JSONField(
        null=True, blank=True,
        verbose_name="同步地域", help_text="同步地域列表JSON，如['ap-guangzhou','ap-shanghai']",
        db_comment="同步地域"
    )
    sync_services = models.JSONField(
        null=True, blank=True,
        verbose_name="同步服务", help_text="同步服务列表JSON，如['cvm','billing']",
        db_comment="同步服务"
    )
    sync_interval_minutes = models.IntegerField(
        default=360, null=True, blank=True,
        verbose_name="同步间隔(分钟)", help_text="自动同步间隔，默认360分钟",
        db_comment="同步间隔(分钟)"
    )
    last_sync_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="最近同步时间", help_text="最近一次同步完成时间",
        db_comment="最近同步时间"
    )
    last_sync_status = models.CharField(
        max_length=20, null=True, blank=True,
        choices=(('success', '成功'), ('failed', '失败'), ('partial', '部分成功')),
        verbose_name="最近同步状态", help_text="最近同步状态",
        db_comment="最近同步状态"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )

    class Meta:
        db_table = f"{table_prefix}cloud_platform"
        verbose_name = "云平台账号"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return f"{self.name} - {self.account_alias or self.account_id}"


class Registrar(CoreModel):
    """
    域名注册商表

    管理域名注册商账户信息，记录注册商的基本信息和归属。
    """
    name = models.CharField(
        max_length=100,
        verbose_name="注册商名称", help_text="注册商名称：腾讯云/阿里云/美橙/易名/GoDaddy等",
        db_comment="注册商名称"
    )
    account_alias = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="注册账户别名", help_text="注册账户别名",
        db_comment="注册账户别名"
    )
    account_id = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name="注册账户ID", help_text="注册账户ID",
        db_comment="注册账户ID"
    )
    company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="归属主体公司", help_text="注册商账户归属主体公司",
        db_comment="归属主体公司"
    )
    contact_person = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="联系人", help_text="联系人姓名",
        db_comment="联系人"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )

    class Meta:
        db_table = f"{table_prefix}registrar"
        verbose_name = "域名注册商"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return f"{self.name} - {self.account_alias or ''}"


class SyncLog(CoreModel):
    """
    API 同步日志表

    记录每次云平台 API 同步的详细结果，包括新增/更新/下线数量和错误详情。
    """
    cloud_platform = models.ForeignKey(
        CloudPlatform, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="云平台账号", help_text="关联云平台账号",
        db_comment="云平台账号"
    )
    sync_type = models.CharField(
        max_length=20,
        choices=(('full', '全量同步'), ('incremental', '增量同步')),
        verbose_name="同步类型", help_text="全量同步 / 增量同步",
        db_comment="同步类型"
    )
    trigger = models.CharField(
        max_length=20,
        choices=(('manual', '手动触发'), ('scheduled', '定时触发')),
        verbose_name="触发方式", help_text="手动触发 / 定时触发",
        db_comment="触发方式"
    )
    status = models.CharField(
        max_length=20,
        choices=(('running', '进行中'), ('success', '成功'), ('failed', '失败'), ('partial', '部分成功')),
        verbose_name="同步状态", help_text="同步状态",
        db_comment="同步状态"
    )
    assets_created = models.IntegerField(
        default=0, null=True, blank=True,
        verbose_name="新增资产数", help_text="本次同步新增资产数量",
        db_comment="新增资产数"
    )
    assets_updated = models.IntegerField(
        default=0, null=True, blank=True,
        verbose_name="更新资产数", help_text="本次同步更新资产数量",
        db_comment="更新资产数"
    )
    assets_terminated = models.IntegerField(
        default=0, null=True, blank=True,
        verbose_name="下线资产数", help_text="本次标记下线资产数量",
        db_comment="下线资产数"
    )
    error_detail = models.JSONField(
        null=True, blank=True,
        verbose_name="错误详情", help_text="错误详情JSON，记录失败的API调用及错误信息",
        db_comment="错误详情"
    )
    started_at = models.DateTimeField(
        verbose_name="开始时间", help_text="同步开始时间",
        db_comment="开始时间"
    )
    finished_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="结束时间", help_text="同步结束时间",
        db_comment="结束时间"
    )

    class Meta:
        db_table = f"{table_prefix}sync_log"
        verbose_name = "同步日志"
        verbose_name_plural = verbose_name
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.cloud_platform} - {self.sync_type} - {self.status}"


class BalanceRecord(CoreModel):
    """
    账户余额记录表

    记录每次云平台余额查询的结果，形成余额历史数据。
    """
    cloud_platform = models.ForeignKey(
        CloudPlatform, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="云平台账号", help_text="关联云平台账号",
        db_comment="云平台账号"
    )
    cash_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="现金余额", help_text="可用现金余额",
        db_comment="现金余额"
    )
    voucher_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="代金券余额", help_text="代金券余额",
        db_comment="代金券余额"
    )
    credit_balance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="信用额度", help_text="信用额度",
        db_comment="信用额度"
    )
    frozen_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="冻结金额", help_text="冻结金额",
        db_comment="冻结金额"
    )
    total_balance = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="总可用余额", help_text="总可用余额（现金+代金券）",
        db_comment="总可用余额"
    )
    currency = models.CharField(
        max_length=10, default='CNY',
        verbose_name="币种", help_text="币种：CNY / USD，默认CNY",
        db_comment="币种"
    )
    recorded_at = models.DateTimeField(
        verbose_name="记录时间", help_text="云平台查询时间",
        db_comment="记录时间"
    )

    class Meta:
        db_table = f"{table_prefix}balance_record"
        verbose_name = "余额记录"
        verbose_name_plural = verbose_name
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['cloud_platform', 'recorded_at'], name='idx_balance_platform_time'),
        ]

    def __str__(self):
        return f"{self.cloud_platform} - {self.total_balance} {self.currency}"
