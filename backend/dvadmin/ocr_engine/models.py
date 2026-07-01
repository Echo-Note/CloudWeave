"""
OCR 异步任务模型 — 追踪批量识别任务的执行状态

状态流转: 0(已创建) → 1(进行中) → 2(完成) / 3(失败)
"""
from django.db import models


class OCRTask(models.Model):
    """OCR 识别异步任务"""

    STATUS_CHOICES = (
        (0, "已创建"),
        (1, "进行中"),
        (2, "已完成"),
        (3, "失败"),
    )

    task_name = models.CharField(
        max_length=255, verbose_name="任务名称", help_text="任务名称"
    )
    task_status = models.SmallIntegerField(
        default=0, choices=STATUS_CHOICES,
        verbose_name="任务状态", help_text="0=已创建 1=进行中 2=已完成 3=失败"
    )
    image_urls = models.JSONField(
        default=list, verbose_name="图片URL列表", help_text="待识别的营业执照图片URL列表"
    )
    results = models.JSONField(
        default=list, verbose_name="识别结果",
        help_text="[{url: ..., data: {...}, error: ...}, ...]"
    )
    total = models.PositiveIntegerField(
        default=0, verbose_name="总数", help_text="待识别图片总数"
    )
    success = models.PositiveIntegerField(
        default=0, verbose_name="成功数", help_text="识别成功的图片数"
    )
    error_message = models.TextField(
        blank=True, default="", verbose_name="错误信息"
    )
    creator = models.CharField(
        max_length=150, default="", verbose_name="创建人"
    )
    create_datetime = models.DateTimeField(
        auto_now_add=True, verbose_name="创建时间"
    )
    update_datetime = models.DateTimeField(
        auto_now=True, verbose_name="更新时间"
    )

    class Meta:
        db_table = "ocr_task"
        verbose_name = "OCR 识别任务"
        verbose_name_plural = verbose_name
        ordering = ["-create_datetime"]

    def __str__(self):
        return f"OCR Task #{self.pk} - {self.task_name}"
