"""
云平台账号 — API 视图
"""
from dvadmin.cloud.models import CloudPlatform
from dvadmin.cloud.serializers.cloud_platform import (
    CloudPlatformExportSerializer,
    CloudPlatformImportSerializer,
    CloudPlatformSerializer,
)
from dvadmin.utils.viewset import CustomModelViewSet


class CloudPlatformViewSet(CustomModelViewSet):
    """
    云平台账号管理

    list:  查询云平台账号列表（支持分页、过滤、搜索）
    create:  新增云平台账号
    update:  修改云平台账号
    retrieve:  查看云平台账号详情
    destroy:  删除云平台账号
    multiple_delete:  批量删除
    """

    queryset = CloudPlatform.objects.all()
    serializer_class = CloudPlatformSerializer
    import_serializer_class = CloudPlatformImportSerializer
    export_serializer_class = CloudPlatformExportSerializer
    filter_fields = ["name", "account_alias", "company", "sync_enabled", "last_sync_status"]
    search_fields = ["name", "account_alias", "account_id", "contact_person"]
    ordering_fields = "__all__"

    import_field_dict = {
        "name": "平台名称",
        "account_alias": "账号别名",
        "account_id": "账号ID/UIN",
        "contact_person": "联系人",
        "sync_enabled": "启用同步(true/false)",
        "sync_interval_minutes": "同步间隔(分钟)",
        "remark": "备注",
    }

    export_field_label = {
        "id": "ID",
        "name": "平台名称",
        "account_alias": "账号别名",
        "account_id": "账号ID/UIN",
        "company": "归属公司ID",
        "company_name": "归属公司",
        "contact_person": "联系人",
        "sync_enabled": "启用同步",
        "sync_regions": "同步地域",
        "sync_services": "同步服务",
        "sync_interval_minutes": "同步间隔(分钟)",
        "last_sync_at": "最近同步时间",
        "last_sync_status": "最近同步状态",
        "remark": "备注",
        "creator_name": "创建人",
        "modifier_name": "修改人",
        "create_datetime": "创建时间",
        "update_datetime": "更新时间",
    }
