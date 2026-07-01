"""
营业执照结构化解析 — OCR 文本 → 字段提取

适配 PaddleOCR 3.x 输出特征（换行漏字），使用非贪婪正则提取。
"""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_RE_CREDIT_CODE = re.compile(r'[\dA-HJ-NP-Z]{18}')


def parse_business_license(ocr_text: str | list[str]) -> dict[str, Any]:
    """
    从 OCR 文本中提取营业执照字段

    Returns: name, credit_code, legal_person, registered_capital,
             established_date, business_scope, address
    """
    if isinstance(ocr_text, list):
        ocr_text = "\n".join(ocr_text)

    text = ocr_text.replace("\r", "").replace(" ", "")
    no_nl = text.replace("\n", "")
    result: dict[str, Any] = {}

    # 1. 统一社会信用代码 — 直接匹配 18 位
    m = _RE_CREDIT_CODE.search(no_nl)
    if m:
        result["credit_code"] = m.group()

    # 2. 公司名称 — 匹配 "称 xxxx有限公司" (非贪婪)
    m = re.search(r'[称稱]\s*([\u4e00-\u9fff（）()]+?(?:有限公司|有限责任公司|股份有限公司))', no_nl)
    if m:
        result["name"] = m.group(1)
    else:
        m = re.search(r'([\u4e00-\u9fff（）()]+(?:有限公司|有限责任公司|股份有限公司))', no_nl)
        if m:
            result["name"] = m.group(1)

    # 2.5 公司类型 — "型" 后紧跟的有限责任公司/股份有限公司 + 括号可选
    m = re.search(r'型\s*(有限责任公司(?:\([\u4e00-\u9fff]+\))?)', no_nl)
    if not m:
        m = re.search(r'型\s*(股份有限公司(?:\([\u4e00-\u9fff]+\))?)', no_nl)
    if m:
        result["company_type"] = m.group(1)

    # 3. 法定代表人 — 2-3字中文名
    m = re.search(r'法定代表人[：:\s]*([\u4e00-\u9fff]{2,3})', no_nl)
    if m:
        result["legal_person"] = m.group(1)

    # 4. 注册资本 — 截取到 "元整" 为止
    m = re.search(r'注册资本[：:\s]*([\d\u4e00-\u9fff万仟佰拾亿元整]+)', no_nl)
    if m:
        cap = m.group(1)
        # 截断到 "元整" 结束
        end = cap.find("元整")
        if end > 0:
            cap = cap[:end + 2]
        result["registered_capital"] = cap

    # 5. 成立日期 — YYYY年MM月DD日
    m = re.search(r'成立日期[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2})', no_nl)
    if m:
        date_str = m.group(1).replace("年", "-").replace("月", "-")
        result["established_date"] = date_str.strip("-")

    # 6. 地址 — "所" 后跟地址，含路/号/层/室
    m = re.search(r'所[：:\s]*([\u4e00-\u9fff]{2,}(?:市|区)[\u4e00-\u9fff\d\-\—·、]{3,50}?(?:号|层|栋|楼|室))', text)
    if not m:
        m = re.search(r'([\u4e00-\u9fff]{2,}(?:市|区)[\u4e00-\u9fff\d\-\—·、]{3,50}?(?:号|层|栋|楼|室))', text)
    if m:
        result["address"] = m.group(1)

    # 7. 经营范围 — "经营范围" 和 "许可项目" 之间的内容 (或到最后)
    # 营业执照上经营范围一般在 "经营范围" 之后 "登记机关" 或网址之前
    m = re.search(r'经营范围[：:\s]*', text)
    if m:
        scope_start = m.end()
        scope_text = text[scope_start:]
        # 截止到 "登记机关" 或 "国家市场" 或 URL
        end_m = re.search(r'登记机关|国家市场|\.gov|http', scope_text)
        scope = scope_text[:end_m.start()] if end_m else scope_text
        scope = scope.replace("\n", "").strip()
        # 清理 "许可项目:" "一般项目:" 前缀
        scope = re.sub(r'(许可|一般)项目[：:]', '', scope)
        # 截断合理长度
        if len(scope) > 300:
            scope = scope[:300]
        result["business_scope"] = scope

    # === 后处理 ===

    # 标准化注册资本数字
    if capital := result.get("registered_capital"):
        num = re.search(r'[\d.]+', capital)
        if num:
            result["registered_capital"] = num.group()

    logger.info(f"营业执照解析: {len(result)} 个字段={[k for k in result]}")
    return result
