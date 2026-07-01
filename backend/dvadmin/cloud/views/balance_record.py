"""
余额记录 — API 视图（只读）
"""
from rest_framework.decorators import action

from dvadmin.cloud.models import BalanceRecord
from dvadmin.cloud.serializers.balance_record import BalanceRecordSerializer
from dvadmin.utils.json_response import DetailResponse
from dvadmin.utils.viewset import CustomModelViewSet


class BalanceRecordViewSet(CustomModelViewSet):
    """
    余额记录（只读）

    list:  查询余额记录列表（支持分页、过滤）
    retrieve:  查看余额记录详情
    latest:  获取各云平台最新余额汇总
    """

    queryset = BalanceRecord.objects.all()
    serializer_class = BalanceRecordSerializer
    filter_fields = ["cloud_platform", "currency"]
    search_fields = ["cloud_platform__name"]
    ordering_fields = "__all__"
    # 只读：禁用增删改
    http_method_names = ["get", "head", "options"]

    @action(methods=["GET"], detail=False)
    def latest(self, request):
        """
        获取各云平台最新一条余额记录汇总

        用于仪表盘展示当前各账号余额情况。
        返回: [{cloud_platform_id, cloud_platform_name, total_balance, currency, recorded_at}]
        """
        from django.db.models import Max

        # 子查询：每个云平台最新记录的 recorded_at
        latest_map = (
            BalanceRecord.objects.values("cloud_platform_id")
            .annotate(latest_at=Max("recorded_at"))
        )
        result = []
        for item in latest_map:
            record = (
                BalanceRecord.objects
                .select_related("cloud_platform")
                .filter(cloud_platform_id=item["cloud_platform_id"], recorded_at=item["latest_at"])
                .first()
            )
            if record:
                result.append({
                    "cloud_platform_id": record.cloud_platform_id,
                    "cloud_platform_name": record.cloud_platform.name if record.cloud_platform else None,
                    "total_balance": str(record.total_balance),
                    "cash_balance": str(record.cash_balance) if record.cash_balance else None,
                    "voucher_balance": str(record.voucher_balance) if record.voucher_balance else None,
                    "currency": record.currency,
                    "recorded_at": record.recorded_at,
                })
        return DetailResponse(data=result, msg="获取成功")
