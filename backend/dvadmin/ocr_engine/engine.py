"""
PaddleOCR 引擎封装 — 支持图片/PDF、本地文件/URL、单张/并行批量

首次调用自动下载 PP-OCRv4 轻量模型（约 15MB）。
并行模式使用线程池 + 线程本地 OCR 实例。
"""
import io
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, quote
from urllib.request import urlopen

logger = logging.getLogger(__name__)

# 线程本地存储: 每个线程持有独立的 PaddleOCR 实例
_local = threading.local()


def _get_or_create_ocr(lang: str = "ch"):
    """获取当前线程的 PaddleOCR 实例"""
    if not hasattr(_local, "ocr"):
        try:
            from paddleocr import PaddleOCR
            _local.ocr = PaddleOCR(lang=lang)
        except ImportError:
            raise RuntimeError(
                "PaddleOCR 未安装。\n安装: uv add paddlepaddle paddleocr\n或: pip install paddlepaddle paddleocr"
            )
    return _local.ocr


def _is_pdf(data: bytes) -> bool:
    """检测字节数据是否为 PDF（魔数 %PDF）"""
    return data[:4] == b"%PDF"


def _is_url(path: str) -> bool:
    """判断是否为网络 URL"""
    parsed = urlparse(path)
    return parsed.scheme in ("http", "https")


def _pdf_to_images(pdf_bytes: bytes) -> list[bytes]:
    """
    PDF 转图片 — 每页一张 PNG

    使用 PyMuPDF (fitz)，纯 pip 安装无系统依赖。
    PyMuPDF 为可选依赖，未安装时提示安装命令。
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError(
            "PDF 识别需要 PyMuPDF。安装: uv add pymupdf\n或: pip install pymupdf"
        )

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images: list[bytes] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # 渲染为图片 (dpi=200 平衡清晰度与速度)
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        images.append(img_bytes)
        logger.debug(f"PDF 第 {page_num + 1} 页已转为图片 ({len(img_bytes)} bytes)")

    doc.close()
    return images


def _recognize_lines(ocr_result: list) -> list[str]:
    """从 PaddleOCR 3.x 结果（dict 格式）提取文本行"""
    if not ocr_result:
        return []
    res = ocr_result[0]  # {"rec_texts": [...], "rec_scores": [...], "dt_polys": [...]}
    if not isinstance(res, dict):
        return []
    texts = res.get("rec_texts") or []
    scores = res.get("rec_scores") or []
    lines = []
    for i, t in enumerate(texts):
        s = scores[i] if i < len(scores) else None
        if s is None or float(s) > 0.5:
            lines.append(str(t))
    return lines


class OCREngine:
    """
    OCR 文字识别引擎 — 支持图片/PDF、本地文件/URL

    使用方式:
        from dvadmin.ocr_engine import OCREngine

        engine = OCREngine()

        # 识别本地文件（自动判断图片/PDF）
        lines = engine.recognize_file("/path/to/license.jpg")
        lines = engine.recognize_file("/path/to/license.pdf")

        # 识别 URL
        lines = engine.recognize_url("https://example.com/license.jpg")

        # 识别内存中的字节数据
        lines = engine.recognize_bytes(image_bytes)

        # 并行批量识别
        results = engine.recognize_batch(urls_or_paths, max_workers=4)
    """

    def __init__(self, lang: str = "ch", max_workers: int = 4):
        self.lang = lang
        self.max_workers = max_workers

    # ===================== 数据获取 =====================

    @staticmethod
    def _read(path_or_url: str) -> bytes:
        """统一读取: 本地文件路径 / URL"""
        if _is_url(path_or_url):
            # 对 URL 中的非 ASCII 字符（如中文文件名）做 percent-encoding
            parsed = urlparse(path_or_url)
            encoded_path = quote(parsed.path, safe="/%")
            safe_url = parsed._replace(path=encoded_path).geturl()
            with urlopen(safe_url, timeout=30) as resp:
                return resp.read()
        # 本地文件
        p = Path(path_or_url)
        if not p.exists():
            raise FileNotFoundError(f"文件不存在: {path_or_url}")
        return p.read_bytes()

    # ===================== 单文件识别 =====================

    def recognize_file(self, path_or_url: str) -> list[str]:
        """
        识别文件中的文字 — 自动判断图片/PDF

        Args:
            path_or_url: 本地文件路径或 HTTP(S) URL

        Returns:
            文字行列表
        """
        data = self._read(path_or_url)
        return self.recognize_bytes(data)

    def recognize_url(self, image_url: str) -> list[str]:
        """识别 URL 指向的图片文字（向下兼容）"""
        return self.recognize_file(image_url)

    def recognize_bytes(self, data: bytes) -> list[str]:
        """
        识别内存中的图片/PDF 文字

        - 图片 (jpg/png): 直接 OCR
        - PDF: 逐页转为图片后 OCR，结果合并
        """
        if _is_pdf(data):
            return self._recognize_pdf(data)
        return self._recognize_image(data)

    def _recognize_image(self, image_bytes: bytes) -> list[str]:
        """OCR 识别单张图片 — PaddleOCR 3.x predict 接受 ndarray 或文件路径"""
        import numpy as np
        from PIL import Image as PILImage

        img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(img)

        ocr = _get_or_create_ocr(self.lang)
        try:
            result = ocr.predict(img_np)
        except AttributeError:
            result = ocr.ocr(img_np)
        return _recognize_lines(result)

    def _recognize_pdf(self, pdf_bytes: bytes) -> list[str]:
        """OCR 识别 PDF（逐页转图片后识别并合并）"""
        images = _pdf_to_images(pdf_bytes)
        if not images:
            return []

        all_lines: list[str] = []
        for i, img_bytes in enumerate(images):
            page_lines = self._recognize_image(img_bytes)
            if page_lines:
                if i > 0:
                    all_lines.append(f"--- 第 {i + 1} 页 ---")
                all_lines.extend(page_lines)
            logger.debug(f"PDF 第 {i + 1} 页 OCR: {len(page_lines)} 行")

        return all_lines

    # ===================== 并行批量识别 =====================

    def _recognize_one(self, path_or_url: str) -> tuple[str, list[str]]:
        """在子线程中识别单个文件"""
        try:
            lines = self.recognize_file(path_or_url)
            return (path_or_url, lines)
        except Exception as e:
            logger.error(f"OCR 识别失败 [{path_or_url}]: {e}")
            return (path_or_url, [])

    def recognize_batch(
        self, sources: list[str], max_workers: int | None = None
    ) -> list[tuple[str, list[str]]]:
        """
        并行批量识别（支持本地文件和 URL 混合）

        Args:
            sources: 文件路径/URL 列表
            max_workers: 最大并行线程数

        Returns:
            [(source, text_lines), ...] 保持输入顺序
        """
        workers = max_workers or self.max_workers
        workers = min(workers, len(sources))

        logger.info(f"开始并行 OCR: {len(sources)} 个文件, {workers} 线程")

        results: list[tuple[str, list[str]]] = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._recognize_one, src): src
                for src in sources
            }
            for future in as_completed(futures):
                results.append(future.result())

        # 按输入顺序排序
        order = {src: idx for idx, src in enumerate(sources)}
        results.sort(key=lambda x: order.get(x[0], 999))

        success = sum(1 for _, lines in results if lines)
        logger.info(f"并行 OCR 完成: {success}/{len(sources)} 成功")
        return results
