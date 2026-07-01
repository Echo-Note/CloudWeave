"""
域名注册商 — API 视图
"""
from dvadmin.cloud.models import Registrar
from dvadmin.cloud.serializers.registrar import (
    RegistrarExportSerializer,
    RegistrarImportSerializer,
    RegistrarSerializer,
)
from dvadmin.utils.viewset import CustomModelViewSet


class RegistrarViewSet(CustomModelViewSet):
    """
    域名注册商管理

    云厂商注册商（腾讯云/阿里云）通过 cloud_platform 关联复用云平台账号密钥，
    独立注册商（GoDaddy/易名）cloud_platform 留空。

    list:  查询域名注册商列表（支持分页、过滤、搜索）
    create:  新增域名注册商
    update:  修改域名注册商
    retrieve:  查看域名注册商详情
    destroy:  删除域名注册商
    multiple_delete:  批量删除
    """

    queryset = Registrar.objects.all()
    serializer_class = RegistrarSerializer
    import_serializer_class = RegistrarImportSerializer
    export_serializer_class = RegistrarExportSerializer
    filter_fields = ["name", "account_alias", "company", "cloud_platform"]
    search_fields = ["name", "account_alias", "account_id", "contact_person"]
    ordering_fields = "__all__"

    import_field_dict = {
        "name": "注册商名称",
        "account_alias": "注册账户别名",
        "account_id": "注册账户ID",
        "cloud_platform": "关联云平台ID",
        "contact_person": "联系人",
        "remark": "备注",
    }

    export_field_label = {
        "id": "ID",
        "name": "注册商名称",
        "account_alias": "注册账户别名",
        "account_id": "注册账户ID",
        "cloud_platform": "关联云平台ID",
        "cloud_platform_name": "关联云平台",
        "company": "归属公司ID",
        "company_name": "归属公司",
        "contact_person": "联系人",
        "remark": "备注",
        "creator_name": "创建人",
        "modifier_name": "修改人",
        "create_datetime": "创建时间",
        "update_datetime": "更新时间",
    }
