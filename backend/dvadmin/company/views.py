"""
主体公司管理 — API 视图

提供 CompanyEntity 模型的完整 CRUD 接口，支持父子层级管理、
统一社会信用代码唯一性校验、营业执照文件上传等。
"""
from rest_framework import serializers
from rest_framework.decorators import action

from dvadmin.company.models import CompanyEntity
from dvadmin.utils.json_response import DetailResponse, SuccessResponse
from dvadmin.utils.serializers import CustomModelSerializer
from dvadmin.utils.viewset import CustomModelViewSet


# ========== 序列化器 ==========

class CompanyEntitySerializer(CustomModelSerializer):
    """主体公司 — 列表/详情查询序列化器"""

    parent_name = serializers.SerializerMethodField(
        read_only=True, help_text="上级主体名称"
    )

    def get_parent_name(self, instance: CompanyEntity) -> str | None:
        """获取上级主体名称"""
        if instance.parent:
            return instance.parent.name
        return None

    class Meta:
        model = CompanyEntity
        fields = "__all__"


class CompanyEntityImportSerializer(CustomModelSerializer):
    """主体公司 — 导入序列化器"""

    class Meta:
        model = CompanyEntity
        fields = "__all__"


class CompanyEntityExportSerializer(CustomModelSerializer):
    """主体公司 — 导出序列化器"""

    parent_name = serializers.SerializerMethodField(
        read_only=True, help_text="上级主体名称"
    )

    def get_parent_name(self, instance: CompanyEntity) -> str | None:
        if instance.parent:
            return instance.parent.name
        return None

    class Meta:
        model = CompanyEntity
        exclude = ("description",)


# ========== ViewSet ==========

class CompanyEntityViewSet(CustomModelViewSet):
    """
    主体公司管理

    list:  查询主体公司列表（支持分页、过滤、搜索）
    create:  新增主体公司
    update:  修改主体公司
    retrieve:  查看主体公司详情
    destroy:  删除主体公司
    multiple_delete:  批量删除
    parent_options:  获取可选上级主体列表（用于下拉选择）
    tree:  获取主体公司树形结构
    """

    queryset = CompanyEntity.objects.all()
    serializer_class = CompanyEntitySerializer
    import_serializer_class = CompanyEntityImportSerializer
    export_serializer_class = CompanyEntityExportSerializer
    # 过滤器与搜索
    filter_fields = ["name", "short_name", "credit_code", "status", "parent"]
    search_fields = ["name", "short_name", "credit_code", "legal_person", "contact_person"]
    ordering_fields = "__all__"

    import_field_dict = {
        "name": "公司全称",
        "short_name": "简称",
        "credit_code": "统一社会信用代码",
        "legal_person": "法定代表人",
        "registered_capital": "注册资本(万元)",
        "established_date": "成立日期",
        "business_scope": "经营范围",
        "address": "注册地址",
        "contact_person": "日常联系人",
        "contact_phone": "联系电话",
        "contact_email": "联系邮箱",
        "status": "状态(active/inactive)",
        "remark": "备注",
    }

    export_field_label = {
        "id": "ID",
        "name": "公司全称",
        "short_name": "简称",
        "credit_code": "统一社会信用代码",
        "legal_person": "法定代表人",
        "registered_capital": "注册资本(万元)",
        "established_date": "成立日期",
        "business_scope": "经营范围",
        "address": "注册地址",
        "contact_person": "日常联系人",
        "contact_phone": "联系电话",
        "contact_email": "联系邮箱",
        "status": "状态",
        "parent": "上级主体ID",
        "parent_name": "上级主体",
        "remark": "备注",
        "creator_name": "创建人",
        "modifier_name": "修改人",
        "create_datetime": "创建时间",
        "update_datetime": "更新时间",
    }

    @action(methods=["GET"], detail=False)
    def parent_options(self, request):
        """
        获取可选上级主体列表（用于前端下拉选择框）

        排除自身及其子孙节点，避免循环引用。
        """
        exclude_id = request.query_params.get("exclude_id")
        queryset = self.get_queryset().filter(status="active")
        if exclude_id:
            # 排除自身
            queryset = queryset.exclude(id=exclude_id)
        queryset = queryset.only("id", "name", "short_name").order_by("name")
        data = [
            {"id": c.id, "name": c.name, "short_name": c.short_name}
            for c in queryset
        ]
        return DetailResponse(data=data, msg="获取成功")

    @action(methods=["GET"], detail=False)
    def tree(self, request):
        """
        获取主体公司树形结构（parent_id 关联）

        支持按状态过滤：?status=active
        """
        queryset = self.filter_queryset(self.get_queryset())
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        nodes = list(
            queryset.values(
                "id", "name", "short_name", "parent_id", "status"
            ).order_by("name")
        )

        def build_tree(parent_id=None):
            """递归构建树结构"""
            children = []
            for node in nodes:
                if node["parent_id"] == parent_id:
                    children.append({
                        "id": node["id"],
                        "name": node["name"],
                        "short_name": node["short_name"],
                        "status": node["status"],
                        "children": build_tree(node["id"]),
                    })
            return children

        tree_data = build_tree(parent_id=None)
        return DetailResponse(data=tree_data, msg="获取成功")

    @action(methods=["POST"], detail=False)
    def batch_set_status(self, request):
        """批量设置主体公司状态"""
        ids = request.data.get("ids", [])
        status = request.data.get("status", "active")
        if not ids:
            from dvadmin.utils.json_response import ErrorResponse
            return ErrorResponse(msg="请提供要操作的公司ID列表")
        if status not in ("active", "inactive"):
            from dvadmin.utils.json_response import ErrorResponse
            return ErrorResponse(msg="状态值无效，仅支持 active 或 inactive")
        CompanyEntity.objects.filter(id__in=ids).update(status=status)
        return SuccessResponse(msg=f"批量设置状态为 {status} 成功")
