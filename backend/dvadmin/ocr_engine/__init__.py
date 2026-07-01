"""
OCR 引擎 — 基于 PaddleOCR 的公共文字识别模块

纯本地运行，无需联网，无 API Key 依赖。
提供: 图片文字识别、营业执照结构化提取。
各业务模块通过 import 直接调用，无需 HTTP 请求。
"""
from dvadmin.ocr_engine.engine import OCREngine
from dvadmin.ocr_engine.license_parser import parse_business_license

__all__ = ["OCREngine", "parse_business_license"]
