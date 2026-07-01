"""
OCR 异步 Celery 任务

并行批量识别营业执照，结果写入 OCRTask 模型。
"""
import logging

from application.celery import app
from dvadmin.ocr_engine.models import OCRTask

logger = logging.getLogger(__name__)


@app.task
def async_ocr_recognize(task_id: int):
    """
    OCR 营业执照异步识别任务

    状态流转: 0 → (设为1) → 并行识别 → 写入结果 → 2 / 3

    OCRTask.image_urls 字段复用存储 file_ids 列表。
    通过 FileList 主键读取文件，自动适配本地/S3/COS 存储后端。

    Args:
        task_id: OCRTask 主键
    """
    instance = OCRTask.objects.get(pk=task_id)
    instance.task_status = 1  # 进行中
    instance.save()

    try:
        from dvadmin.ocr_engine import OCREngine, parse_business_license
        from dvadmin.system.models import FileList

        file_ids = instance.image_urls  # 复用字段存储 file_ids
        results = []
        success_count = 0

        for fid in file_ids:
            try:
                file_obj = FileList.objects.get(pk=fid)
                if not file_obj.url:
                    results.append({"file_id": fid, "data": None, "error": "文件记录无关联文件"})
                    continue
                with file_obj.url.open("rb") as f:
                    image_data = f.read()

                engine = OCREngine()
                lines = engine.recognize_bytes(image_data)
                if lines:
                    data = parse_business_license(lines)
                    results.append({"file_id": fid, "data": data, "error": None})
                    if data:
                        success_count += 1
                else:
                    results.append({"file_id": fid, "data": None, "error": "OCR 未识别到文字"})
            except Exception as e:
                results.append({"file_id": fid, "data": None, "error": str(e)[:200]})

        instance.results = results
        instance.total = len(results)
        instance.success = success_count
        instance.task_status = 2  # 完成

    except ImportError:
        instance.task_status = 3
        instance.error_message = "OCR 引擎未安装（paddlepaddle / paddleocr）"

    except Exception as e:
        instance.task_status = 3
        instance.error_message = str(e)[:500]
        logger.exception(f"OCR 异步任务 #{task_id} 失败")

    instance.save()
    logger.info(
        f"OCR 异步任务 #{task_id} 完成: {instance.success}/{instance.total} 张成功"
    )
