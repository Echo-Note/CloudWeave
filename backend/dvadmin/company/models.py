"""
主体公司管理 — 数据模型

CompanyEntity 是全系统通用的组织架构实体，统一承载域名归属、
云平台账号归属、办公资产归属、ICP 备案主体、项目归属等场景。
"""
from django.db import models

from dvadmin.utils.models import CoreModel, table_prefix


class CompanyEntity(CoreModel):
    """
    主体公司表 — 全系统通用组织架构

    各业务模块通过 ForeignKey 关联此表，实现跨模块统一查询。
    支持父子级层级（集团 → 子公司 → 孙公司），便于权限隔离和数据归集。
    """
    name = models.CharField(
        max_length=200, unique=True,
        verbose_name="公司全称", help_text="公司全称，如'XX科技有限公司'",
        db_comment="公司全称"
    )
    short_name = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="简称", help_text="简称，如'子公司A'",
        db_comment="简称"
    )
    credit_code = models.CharField(
        max_length=50, null=True, blank=True, unique=True,
        verbose_name="统一社会信用代码", help_text="18位统一社会信用代码，不为空时唯一",
        db_comment="统一社会信用代码"
    )
    legal_person = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="法定代表人", help_text="法定代表人姓名",
        db_comment="法定代表人"
    )
    registered_capital = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        verbose_name="注册资本(万元)", help_text="注册资本，单位为万元",
        db_comment="注册资本(万元)"
    )
    established_date = models.DateField(
        null=True, blank=True,
        verbose_name="成立日期", help_text="公司成立日期",
        db_comment="成立日期"
    )
    business_scope = models.TextField(
        null=True, blank=True,
        verbose_name="经营范围", help_text="经营范围",
        db_comment="经营范围"
    )
    address = models.TextField(
        null=True, blank=True,
        verbose_name="注册地址", help_text="注册地址",
        db_comment="注册地址"
    )
    contact_person = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="日常联系人", help_text="日常联系人姓名",
        db_comment="日常联系人"
    )
    contact_phone = models.CharField(
        max_length=20, null=True, blank=True,
        verbose_name="联系电话", help_text="联系电话",
        db_comment="联系电话"
    )
    contact_email = models.EmailField(
        null=True, blank=True,
        verbose_name="联系邮箱", help_text="联系邮箱",
        db_comment="联系邮箱"
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="上级主体", help_text="上级主体（集团→子公司→孙公司层级）",
        db_comment="上级主体"
    )
    status = models.CharField(
        max_length=20, default='active',
        choices=(('active', '启用'), ('inactive', '停用')),
        verbose_name="状态", help_text="状态：active(启用) / inactive(停用)",
        db_comment="状态"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )

    class Meta:
        db_table = f"{table_prefix}company_entity"
        verbose_name = "主体公司"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return self.name
