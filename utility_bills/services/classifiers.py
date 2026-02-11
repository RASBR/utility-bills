# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

from typing import Literal

from ..models import UtilityType


LayoutType = Literal["electricity_summary", "electricity_detailed", "water_unknown", "unknown"]


def classify_layout(raw_text: str) -> LayoutType:
    """Lightweight heuristics to route to the right parser.

    - Summary screenshots: have labels like 'Bill No' / 'Previous reading' or Arabic equivalents.
    - Detailed electricity: contains 'المصدرة إلى الشبكة' (export to grid) or dinar/fils tables.
    """
    t = raw_text or ""
    if "المصدرة" in t or "المستجرة" in t or "قراءة عداد الطاقة" in t:
        return "electricity_detailed"
    if "Bill No" in t or "Previous reading" in t or "القراءة السابقة" in t:
        return "electricity_summary"
    return "unknown"
