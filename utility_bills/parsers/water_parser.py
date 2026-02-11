# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

from ..services.normalizers import normalize_digits


@dataclass
class WaterParsed:
    meter_number: Optional[str]
    period_start: Optional[date]
    period_end: Optional[date]
    previous_reading: Optional[int]
    current_reading: Optional[int]
    billed_m3: Optional[int]


def parse_water_text(raw_text: str) -> WaterParsed:
    t = normalize_digits(raw_text or "")
    meter = None
    m = re.search(r"رقم\s*العداد\s*(\d+)", t)
    if m:
        meter = m.group(1)

    prev = None
    cur = None
    m = re.search(r"القراءة\s*السابقة\s*(\d+)", t)
    if m:
        prev = int(m.group(1))
    m = re.search(r"القراءة\s*الحالية\s*(\d+)", t)
    if m:
        cur = int(m.group(1))

    billed = None
    m = re.search(r"الكمية\s*المفوترة\s*(\d+)", t)
    if m:
        billed = int(m.group(1))

    return WaterParsed(
        meter_number=meter,
        period_start=None,
        period_end=None,
        previous_reading=prev,
        current_reading=cur,
        billed_m3=billed,
    )
