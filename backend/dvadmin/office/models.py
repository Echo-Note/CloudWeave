"""
办公资产管理 — 数据模型

面向集团公司多主体场景，对办公电脑、手机、SIM卡、平板等设备进行
统一登记、全生命周期追踪与流程化管控。
"""
from django.conf import settings
from django.db import models

from dvadmin.utils.models import CoreModel, table_name


class AssetCategory(CoreModel):
    """
    资产类型表

    支持预置类型和自定义类型，每种类型可配置专属字段Schema。
    预置类型不可删除，归档后不可新增该类资产。
    """
    name = models.CharField(
        max_length=100, unique=True,
        verbose_name="类型名称", help_text="类型名称，唯一",
        db_comment="类型名称"
    )
    icon = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="图标标识", help_text="图标标识",
        db_comment="图标标识"
    )
    is_preset = models.BooleanField(
        default=False,
        verbose_name="系统预置", help_text="是否系统预置，预置不可删除",
        db_comment="系统预置"
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name="是否启用", help_text="是否启用，默认True",
        db_comment="是否启用"
    )
    custom_fields_schema = models.JSONField(
        default=list,
        verbose_name="自定义字段定义",
        help_text=(
            "自定义字段定义JSON数组。每个字段含：key(字段键名)、label(显示名称)、"
            "type(text/number/date/select/boolean)、required(是否必填)、"
            "options(select类型时的选项数组)、order(排序)"
        ),
        db_comment="自定义字段定义"
    )

    class Meta:
        db_table = table_name("office", "asset_category")
        verbose_name = "资产类型"
        verbose_name_plural = verbose_name
        ordering = ['-is_preset', 'name']

    def __str__(self):
        return self.name


class OfficeAsset(CoreModel):
    """
    办公资产表

    办公设备的核心信息、所属主体、使用人、采购信息和自定义字段值。
    支持二维码标签，软删除。
    """
    is_soft_delete = True

    asset_code = models.CharField(
        max_length=50, unique=True,
        verbose_name="资产编号", help_text="资产编号，自动生成（如ZC-20260630-0001），唯一",
        db_comment="资产编号"
    )
    name = models.CharField(
        max_length=200,
        verbose_name="资产名称", help_text="资产名称，如'ThinkPad X1 Carbon'",
        db_comment="资产名称"
    )
    category = models.ForeignKey(
        AssetCategory, on_delete=models.PROTECT,
        db_constraint=False,
        verbose_name="所属资产类型", help_text="所属资产类型",
        db_comment="所属资产类型"
    )
    company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.PROTECT,
        db_constraint=False,
        verbose_name="所属主体公司", help_text="所属主体公司",
        db_comment="所属主体公司"
    )
    status = models.CharField(
        max_length=20, default='in_stock',
        choices=(
            ('in_stock', '在库'),
            ('assigned', '已领用'),
            ('borrowed', '借用中'),
            ('transferring', '调拨中'),
            ('repairing', '维修中'),
            ('scrapped', '已报废'),
        ),
        verbose_name="资产状态", help_text="资产状态",
        db_comment="资产状态"
    )
    current_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='office_assets_in_use', db_constraint=False,
        verbose_name="当前使用人", help_text="当前使用人（领用或借用中）",
        db_comment="当前使用人"
    )
    location = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name="存放位置", help_text="存放位置，如'A栋3楼301室'",
        db_comment="存放位置"
    )
    purchase_date = models.DateField(
        null=True, blank=True,
        verbose_name="采购日期", help_text="采购日期",
        db_comment="采购日期"
    )
    purchase_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="采购金额", help_text="采购金额",
        db_comment="采购金额"
    )
    supplier = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name="供应商", help_text="供应商",
        db_comment="供应商"
    )
    invoice_number = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="发票号", help_text="发票号",
        db_comment="发票号"
    )
    warranty_expire = models.DateField(
        null=True, blank=True,
        verbose_name="保修截止日期", help_text="保修截止日期",
        db_comment="保修截止日期"
    )
    custom_fields_data = models.JSONField(
        null=True, blank=True,
        verbose_name="自定义字段值",
        help_text="自定义字段实际值JSON，按category.custom_fields_schema校验",
        db_comment="自定义字段值"
    )
    qr_code_url = models.URLField(
        null=True, blank=True,
        verbose_name="二维码URL", help_text="资产二维码图片URL",
        db_comment="二维码URL"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )
    is_deleted = models.BooleanField(
        default=False, db_index=True,
        verbose_name="软删除标记", help_text="软删除标记",
        db_comment="软删除标记"
    )

    class Meta:
        db_table = table_name("office", "asset")
        verbose_name = "办公资产"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']
        indexes = [
            models.Index(fields=['company', 'category'], name='idx_office_asset_company_cat'),
            models.Index(fields=['status'], name='idx_office_asset_status'),
            models.Index(fields=['current_user'], name='idx_office_asset_user'),
        ]

    def __str__(self):
        return f"[{self.asset_code}] {self.name}"


class SimCardInfo(CoreModel):
    """
    SIM 卡实名信息表

    仅限类型为"手机卡"的办公资产拥有此关联记录。
    身份证号加密存储，身份证号哈希用于"一人多卡"查询。
    """
    asset = models.OneToOneField(
        OfficeAsset, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联资产", help_text="关联的SIM卡资产（category为手机卡）",
        db_comment="关联资产"
    )
    phone_number = models.CharField(
        max_length=20,
        verbose_name="手机号", help_text="手机号",
        db_comment="手机号"
    )
    real_name = models.CharField(
        max_length=50,
        verbose_name="实名人姓名", help_text="实名人姓名",
        db_comment="实名人姓名"
    )
    id_number = models.CharField(
        max_length=100,
        verbose_name="身份证号", help_text="身份证号（AES-256加密存储）",
        db_comment="身份证号"
    )
    id_number_hash = models.CharField(
        max_length=64,
        verbose_name="身份证号哈希", help_text="身份证号SHA-256哈希（用于一人多卡查询）",
        db_comment="身份证号哈希"
    )
    id_card_front = models.FileField(
        null=True, blank=True,
        verbose_name="身份证正面照片", help_text="身份证正面照片（加密存储）",
        db_comment="身份证正面照片"
    )
    id_card_back = models.FileField(
        null=True, blank=True,
        verbose_name="身份证反面照片", help_text="身份证反面照片（加密存储）",
        db_comment="身份证反面照片"
    )
    id_card_expire = models.DateField(
        null=True, blank=True,
        verbose_name="身份证有效期", help_text="身份证有效期截止日",
        db_comment="身份证有效期"
    )
    carrier = models.CharField(
        max_length=20,
        choices=(
            ('china_mobile', '中国移动'),
            ('china_unicom', '中国联通'),
            ('china_telecom', '中国电信'),
            ('china_broadnet', '中国广电'),
        ),
        verbose_name="运营商", help_text="运营商",
        db_comment="运营商"
    )
    iccid = models.CharField(
        max_length=30, null=True, blank=True,
        verbose_name="ICCID", help_text="SIM卡ICCID",
        db_comment="ICCID"
    )
    plan_name = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="套餐名称", help_text="套餐名称",
        db_comment="套餐名称"
    )
    monthly_fee = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name="月租费", help_text="月租费",
        db_comment="月租费"
    )
    activation_date = models.DateField(
        null=True, blank=True,
        verbose_name="开卡日期", help_text="开卡日期",
        db_comment="开卡日期"
    )
    contract_end_date = models.DateField(
        null=True, blank=True,
        verbose_name="合约到期日", help_text="合约到期日",
        db_comment="合约到期日"
    )

    class Meta:
        db_table = table_name("office", "sim_card_info")
        verbose_name = "SIM卡实名信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.phone_number} - {self.real_name}"


class AssetBorrowRecord(CoreModel):
    """
    借用记录表

    完整审批闭环：申请 → 主管审批 → 资产管理员确认 → 发放 → 归还验收。
    支持续借和逾期标记。
    """
    asset = models.ForeignKey(
        OfficeAsset, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="借用资产", help_text="借用的资产",
        db_comment="借用资产"
    )
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='borrow_records', db_constraint=False,
        verbose_name="借用人", help_text="借用人",
        db_comment="借用人"
    )
    borrow_reason = models.TextField(
        verbose_name="借用事由", help_text="借用事由",
        db_comment="借用事由"
    )
    expected_return_date = models.DateField(
        verbose_name="预计归还日期", help_text="预计归还日期",
        db_comment="预计归还日期"
    )
    actual_return_date = models.DateField(
        null=True, blank=True,
        verbose_name="实际归还日期", help_text="实际归还日期",
        db_comment="实际归还日期"
    )
    approval_status = models.CharField(
        max_length=20, default='pending',
        choices=(
            ('pending', '待审批'),
            ('approved', '已通过'),
            ('rejected', '已驳回'),
            ('extended', '已续借'),
        ),
        verbose_name="审批状态", help_text="审批状态",
        db_comment="审批状态"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='borrow_approvals', db_constraint=False,
        verbose_name="审批人", help_text="审批人",
        db_comment="审批人"
    )
    approved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="审批时间", help_text="审批时间",
        db_comment="审批时间"
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='borrow_issues', db_constraint=False,
        verbose_name="发放人", help_text="发放人（资产管理员）",
        db_comment="发放人"
    )
    issued_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="发放时间", help_text="发放时间",
        db_comment="发放时间"
    )
    return_status = models.CharField(
        max_length=20, null=True, blank=True,
        choices=(
            ('normal', '正常归还'),
            ('damaged', '有损坏'),
            ('lost', '已丢失'),
        ),
        verbose_name="归还状态", help_text="归还验收结果",
        db_comment="归还状态"
    )
    return_note = models.TextField(
        null=True, blank=True,
        verbose_name="验收备注", help_text="验收备注",
        db_comment="验收备注"
    )
    returned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='borrow_returns', db_constraint=False,
        verbose_name="验收人", help_text="验收人",
        db_comment="验收人"
    )
    is_overdue = models.BooleanField(
        default=False,
        verbose_name="是否逾期", help_text="是否逾期",
        db_comment="是否逾期"
    )

    class Meta:
        db_table = table_name("office", "asset_borrow_record")
        verbose_name = "借用记录"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']
        indexes = [
            models.Index(fields=['asset', 'approval_status'], name='idx_borrow_asset_status'),
            models.Index(fields=['borrower', 'approval_status'], name='idx_borrow_user_status'),
        ]

    def __str__(self):
        return f"{self.borrower} 借用 {self.asset}"


class AssetTransferRecord(CoreModel):
    """
    资产调拨记录表

    支持主体间调拨，记录调出方和调入方，含审批流程。
    """
    asset = models.ForeignKey(
        OfficeAsset, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="调拨资产", help_text="调拨的资产",
        db_comment="调拨资产"
    )
    from_company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.CASCADE,
        related_name='transfers_out', db_constraint=False,
        verbose_name="调出主体", help_text="调出主体",
        db_comment="调出主体"
    )
    to_company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.CASCADE,
        related_name='transfers_in', db_constraint=False,
        verbose_name="调入主体", help_text="调入主体",
        db_comment="调入主体"
    )
    transfer_reason = models.TextField(
        verbose_name="调拨原因", help_text="调拨原因",
        db_comment="调拨原因"
    )
    status = models.CharField(
        max_length=20, default='pending',
        choices=(
            ('pending', '待审批'),
            ('approved', '已通过'),
            ('rejected', '已驳回'),
            ('completed', '已完成'),
        ),
        verbose_name="调拨状态", help_text="调拨状态",
        db_comment="调拨状态"
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transfer_submissions', db_constraint=False,
        verbose_name="申请人", help_text="申请人",
        db_comment="申请人"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transfer_approvals', db_constraint=False,
        verbose_name="审批人", help_text="审批人",
        db_comment="审批人"
    )
    approved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="审批时间", help_text="审批时间",
        db_comment="审批时间"
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transfer_receipts', db_constraint=False,
        verbose_name="调入方接收人", help_text="调入方接收人",
        db_comment="调入方接收人"
    )
    received_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="接收时间", help_text="接收时间",
        db_comment="接收时间"
    )

    class Meta:
        db_table = table_name("office", "asset_transfer_record")
        verbose_name = "资产调拨记录"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return f"{self.asset}: {self.from_company} → {self.to_company}"


class AssetOperationLog(CoreModel):
    """
    资产操作流水表

    记录资产所有状态变更（入库、领用、借用、归还、调拨、报废），
    作为资产详情页"生命周期时间线"的数据源。
    """
    asset = models.ForeignKey(
        OfficeAsset, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="关联资产", help_text="关联资产",
        db_comment="关联资产"
    )
    operation_type = models.CharField(
        max_length=30,
        choices=(
            ('purchase', '采购入库'),
            ('assign', '领用分配'),
            ('borrow', '借用'),
            ('return', '归还'),
            ('transfer', '调拨'),
            ('scrap', '报废'),
            ('repair', '维修'),
        ),
        verbose_name="操作类型", help_text="操作类型",
        db_comment="操作类型"
    )
    from_status = models.CharField(
        max_length=20, null=True, blank=True,
        verbose_name="操作前状态", help_text="操作前状态",
        db_comment="操作前状态"
    )
    to_status = models.CharField(
        max_length=20,
        verbose_name="操作后状态", help_text="操作后状态",
        db_comment="操作后状态"
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='asset_operations', db_constraint=False,
        verbose_name="操作人", help_text="操作人",
        db_comment="操作人"
    )
    detail = models.JSONField(
        null=True, blank=True,
        verbose_name="操作详情", help_text="操作详情JSON（含关联记录ID、备注等）",
        db_comment="操作详情"
    )

    class Meta:
        db_table = table_name("office", "asset_operation_log")
        verbose_name = "资产操作流水"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return f"{self.asset} - {self.get_operation_type_display()}"
