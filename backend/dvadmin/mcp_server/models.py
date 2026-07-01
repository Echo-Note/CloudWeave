"""
MCP 智能集成 — 数据模型

管理 MCP API Key（创建/权限/吊销）和调用审计日志。
"""
from django.conf import settings
from django.db import models

from dvadmin.utils.models import CoreModel

table_prefix = "mcp_"  # 数据库表前缀（App 级别）


class McpApiKey(CoreModel):
    """
    MCP API Key 表

    管理 AI 客户端接入的 API Key，支持只读/读写/管理员三级权限。
    Key 仅在创建时完整展示一次，之后仅存储 SHA-256 哈希。
    """
    name = models.CharField(
        max_length=200,
        verbose_name="Key名称", help_text="Key名称，便于识别（如'CodeBuddy本地开发'）",
        db_comment="Key名称"
    )
    key_hash = models.CharField(
        max_length=255,
        verbose_name="Key哈希", help_text="API Key的SHA-256哈希，原Key仅创建时返回一次",
        db_comment="Key哈希"
    )
    key_prefix = models.CharField(
        max_length=16,
        verbose_name="Key前缀", help_text="Key前缀（前8位），用于列表展示脱敏标识",
        db_comment="Key前缀"
    )
    permission_level = models.CharField(
        max_length=20, default='readonly',
        choices=(
            ('readonly', '只读'),
            ('readwrite', '读写'),
            ('admin', '管理员'),
        ),
        verbose_name="权限级别", help_text="权限级别：readonly(只读)/readwrite(读写)/admin(管理员)",
        db_comment="权限级别"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mcp_keys_created', db_constraint=False,
        verbose_name="创建人", help_text="创建人",
        db_comment="创建人"
    )
    last_used_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="最近使用时间", help_text="最近一次使用时间",
        db_comment="最近使用时间"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否启用", help_text="是否启用，停用后立即拒绝该Key的所有MCP请求",
        db_comment="是否启用"
    )
    expires_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="过期时间", help_text="过期时间（为空则永不过期）",
        db_comment="过期时间"
    )

    class Meta:
        db_table = f"{table_prefix}api_key"
        verbose_name = "MCP API Key"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return f"{self.name} [{self.get_permission_level_display()}] [{'启用' if self.is_active else '停用'}]"


class McpAuditLog(CoreModel):
    """
    MCP 调用审计表

    记录每次 MCP Tool 调用的详细信息：调用者、Tool名称、参数、结果、耗时。
    支持异常检测（高频调用、失败率告警）。
    """
    api_key = models.ForeignKey(
        McpApiKey, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="API Key", help_text="使用的API Key",
        db_comment="API Key"
    )
    tool_name = models.CharField(
        max_length=100,
        verbose_name="Tool名称", help_text="调用的Tool名称",
        db_comment="Tool名称"
    )
    tool_args = models.JSONField(
        verbose_name="请求参数", help_text="请求参数JSON（已脱敏）",
        db_comment="请求参数"
    )
    tool_result_status = models.CharField(
        max_length=20,
        choices=(
            ('success', '成功'),
            ('failed', '失败'),
            ('denied', '拒绝'),
        ),
        verbose_name="执行结果", help_text="执行结果",
        db_comment="执行结果"
    )
    tool_result_summary = models.TextField(
        null=True, blank=True,
        verbose_name="结果摘要", help_text="结果摘要（如'返回12台服务器'）",
        db_comment="结果摘要"
    )
    execution_time_ms = models.IntegerField(
        null=True, blank=True,
        verbose_name="执行耗时(ms)", help_text="执行耗时，单位毫秒",
        db_comment="执行耗时(ms)"
    )
    error_message = models.TextField(
        null=True, blank=True,
        verbose_name="错误信息", help_text="错误信息",
        db_comment="错误信息"
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="来源IP", help_text="请求来源IP",
        db_comment="来源IP"
    )

    class Meta:
        db_table = f"{table_prefix}audit_log"
        verbose_name = "MCP调用审计"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']
        indexes = [
            models.Index(fields=['api_key', 'create_datetime'], name='idx_mcp_audit_key_time'),
            models.Index(fields=['tool_name', 'create_datetime'], name='idx_mcp_audit_tool_time'),
        ]

    def __str__(self):
        return f"{self.api_key} → {self.tool_name} [{self.tool_result_status}]"
