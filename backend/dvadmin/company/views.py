"""
主体公司管理 — API 视图

提供 CompanyEntity 模型的完整 CRUD 接口，支持父子层级管理、
统一社会信用代码唯一性校验、营业执照文件上传等。
"""
from rest_framework import serializers
from rest_framework.decorators import action

from dvadmin.company.models import CompanyEntity
from dvadmin.utils.json_response import DetailResponse, ErrorResponse, SuccessResponse
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

    def to_representation(self, instance):
        """
        输出时将 business_license 相对路径转为可访问 URL

        私有对象存储下，default_storage.url() 会生成带签名的 presigned URL；
        本地存储下返回 /media/... 相对路径，由前端拼接后端地址。
        """
        ret = super().to_representation(instance)
        license_val = ret.get('business_license')
        if license_val and not license_val.startswith('http'):
            from django.core.files.storage import default_storage
            from urllib.parse import unquote
            # 数据库存的是 "media/files/..." 格式，S3Storage 的 key 是去掉 "media/" 前缀的部分
            key = license_val[6:] if license_val.startswith('media/') else license_val
            # 解码 percent-encoding，避免 default_storage.url() 二次编码导致签名失效
            key = unquote(key)
            try:
                ret['business_license'] = default_storage.url(key)
            except Exception:
                pass
        return ret

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
        "company_type": "公司类型",
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
        "company_type": "公司类型",
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

    @action(methods=["GET"], detail=False)
    def ocr_status(self, request):
        """
        检查 OCR 引擎是否可用

        返回: {"available": true/false}
        """
        try:
            from dvadmin.ocr_engine import OCREngine
            OCREngine()
            return SuccessResponse(data={"available": True})
        except ImportError:
            return SuccessResponse(data={"available": False})
        except Exception:
            return SuccessResponse(data={"available": False})

    @action(methods=["POST"], detail=False)
    def recognize_license(self, request):
        """
        OCR 营业执照识别（可选功能，需安装 PaddleOCR）

        传入已上传文件的 ID，由本地 OCR 引擎自动提取公司登记信息。
        通过 FileList 记录的 FileField 读取文件，自动适配本地/S3/COS 存储后端。

        请求体: {"file_id": 15}
        返回:   {"name": "...", "credit_code": "...", ...}
        """
        file_id = request.data.get("file_id")
        if not file_id:
            return ErrorResponse(msg="请提供文件 ID")

        try:
            from dvadmin.ocr_engine import OCREngine, parse_business_license
        except ImportError:
            return ErrorResponse(
                msg="OCR 引擎未安装。请在服务器执行: pip install paddlepaddle paddleocr"
            )

        try:
            image_data = self._read_file_by_id(file_id)
            engine = OCREngine()
            lines = engine.recognize_bytes(image_data)
            if not lines:
                return ErrorResponse(msg="OCR 未识别到文字，请检查图片清晰度")
            result = parse_business_license(lines)
            if not result:
                return ErrorResponse(msg="未能从图像中提取营业执照信息")
            return DetailResponse(data=result, msg="营业执照识别成功")
        except Exception as e:
            return ErrorResponse(msg=f"识别失败: {str(e)}")

    @staticmethod
    def _read_file_by_id(file_id: int | str) -> bytes:
        """
        通过 FileList 主键读取文件字节数据

        FileField.open() 会自动使用配置的存储后端（本地/S3/COS），
        无需关心文件实际存储位置和路径差异。
        """
        from dvadmin.system.models import FileList

        try:
            file_obj = FileList.objects.get(pk=file_id)
        except FileList.DoesNotExist:
            raise FileNotFoundError(f"文件记录不存在: id={file_id}")

        if not file_obj.url:
            raise FileNotFoundError(f"文件记录无关联文件: id={file_id}")

        with file_obj.url.open("rb") as f:
            return f.read()

    @action(methods=["POST"], detail=False)
    def batch_recognize_license(self, request):
        """
        异步批量 OCR 营业执照识别

        单张 ≤1 张时同步返回（快速），多张时提交 Celery 异步任务。

        请求体: {"file_ids": [15, 16, 17]}
        返回:
          同步: {"results": [...], "total": N, "success": M, "async": false}
          异步: {"task_id": 123, "async": true, "msg": "..."}
        轮询: GET /api/company/entity/ocr_task_status/?task_id=123
        """
        file_ids = request.data.get("file_ids", [])
        if not file_ids:
            return ErrorResponse(msg="请提供文件 ID 列表")
        if not isinstance(file_ids, list):
            return ErrorResponse(msg="file_ids 应为数组格式")

        try:
            from dvadmin.ocr_engine import OCREngine, parse_business_license
        except ImportError:
            return ErrorResponse(
                msg="OCR 引擎未安装。请在服务器执行: pip install paddlepaddle paddleocr"
            )

        # 单张图片 → 同步返回（不阻塞太久）
        if len(file_ids) <= 1:
            try:
                image_data = self._read_file_by_id(file_ids[0])
                engine = OCREngine()
                lines = engine.recognize_bytes(image_data)
                if lines:
                    data = parse_business_license(lines)
                    return DetailResponse(
                        data={"results": [{"file_id": file_ids[0], "data": data, "error": None}],
                              "total": 1, "success": 1 if data else 0, "async": False},
                        msg="营业执照识别完成"
                    )
            except Exception as e:
                return ErrorResponse(msg=f"识别失败: {str(e)}")
            return ErrorResponse(msg="OCR 未识别到文字，请检查图片清晰度")

        # 多张 → 异步 Celery 任务
        try:
            from dvadmin.ocr_engine.models import OCRTask
            from dvadmin.ocr_engine.tasks import async_ocr_recognize

            task = OCRTask.objects.create(
                task_name=f"营业执照批量识别 ({len(file_ids)} 张)",
                file_ids=file_ids,
                total=len(file_ids),
                creator=request.user.username if request.user.is_authenticated else "",
            )
            async_ocr_recognize.delay(task.pk)
            return SuccessResponse(
                data={"task_id": task.pk, "async": True, "total": len(file_ids)},
                msg=f"批量识别任务已创建，共 {len(file_ids)} 张图片，请轮询查询结果"
            )
        except Exception as e:
            return ErrorResponse(msg=f"创建识别任务失败: {str(e)}")

    @action(methods=["GET"], detail=False)
    def ocr_task_status(self, request):
        """
        轮询 OCR 异步任务状态

        GET /api/company/entity/ocr_task_status/?task_id=123
        返回: {task_id, status, status_label, total, success, results, error_message}
        """
        task_id = request.query_params.get("task_id")
        if not task_id:
            return ErrorResponse(msg="请提供 task_id 参数")

        try:
            from dvadmin.ocr_engine.models import OCRTask
            task = OCRTask.objects.get(pk=task_id)
        except OCRTask.DoesNotExist:
            return ErrorResponse(msg="任务不存在")

        status_labels = {0: "已创建", 1: "进行中", 2: "已完成", 3: "失败"}
        return DetailResponse(data={
            "task_id": task.pk,
            "status": task.task_status,
            "status_label": status_labels.get(task.task_status, "未知"),
            "total": task.total,
            "success": task.success,
            "results": task.results if task.task_status == 2 else [],
            "error_message": task.error_message,
        }, msg="查询成功")
