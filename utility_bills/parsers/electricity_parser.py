# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from ..services.normalizers import normalize_digits, parse_decimal_maybe


@dataclass
class ElectricityParsed:
    meter_number: Optional[str]
    period_start: Optional[date]
    period_end: Optional[date]
    reading_date: Optional[date]

    import_previous: Optional[int]
    import_current: Optional[int]
    export_previous: Optional[int]
    export_current: Optional[int]
    billed_kwh: Optional[int]

    total_bill_value: Optional[Decimal]
    consumption_value: Optional[Decimal]
    network_services_fees: Optional[Decimal]
    fixed_subsidy_amount: Optional[Decimal]


_DATE_RE = re.compile(r"(\d{4})/(\d{2})/(\d{2})")


def _parse_date(s: str) -> Optional[date]:
    m = _DATE_RE.search(s)
    if not m:
        return None
    y, mo, d = map(int, m.groups())
    return date(y, mo, d)


def parse_electricity_text(raw_text: str) -> ElectricityParsed:
    t = normalize_digits(raw_text or "")

    # Meter number: Arabic / English variants
    meter = None
    m = re.search(r"رقم العداد\s*(\d+)", t)
    if m:
        meter = m.group(1)
    else:
        m = re.search(r"Meter\s*No\s*(\d+)", t, re.IGNORECASE)
        if m:
            meter = m.group(1)

    # Period
    ps = None
    pe = None
    m = re.search(r"من\s*(\d{4}/\d{2}/\d{2})\s*الى\s*(\d{4}/\d{2}/\d{2})", t)
    if m:
        ps = _parse_date(m.group(1))
        pe = _parse_date(m.group(2))
    else:
        m = re.search(r"from\s*(\d{4}/\d{2}/\d{2}).*to\s*(\d{4}/\d{2}/\d{2})", t, re.IGNORECASE)
        if m:
            ps = _parse_date(m.group(1))
            pe = _parse_date(m.group(2))

    rd = None
    m = re.search(r"تاريخ القراءة\s*(\d{4}/\d{2}/\d{2})", t)
    if m:
        rd = _parse_date(m.group(1))
    else:
        m = re.search(r"Reading\s*date\s*(\d{4}/\d{2}/\d{2})", t, re.IGNORECASE)
        if m:
            rd = _parse_date(m.group(1))

    # Summary readings (imported)
    imp_prev = None
    imp_cur = None
    m = re.search(r"القراءة السابقة\s*(\d+)", t)
    if m:
        imp_prev = int(m.group(1))
    m = re.search(r"القراءة الحالية\s*(\d+)", t)
    if m:
        imp_cur = int(m.group(1))

    # Detailed energy table: imported/exported
    exp_prev = None
    exp_cur = None

    # Imported row sometimes: 'المستجرة من الشبكة 16128 15364 764'
    m = re.search(r"المستجرة\s+من\s+الشبكة\s+(\d+)\s+(\d+)\s+(\d+)", t)
    if m:
        imp_cur = int(m.group(1))
        imp_prev = int(m.group(2))

    m = re.search(r"المصدرة\s+إلى\s+الشبكة\s+(\d+)\s+(\d+)\s+(\d+)", t)
    if m:
        exp_cur = int(m.group(1))
        exp_prev = int(m.group(2))

    # Billed quantity
    billed = None
    m = re.search(r"الكمية المفوترة\s*(\-?\d+)", t)
    if m:
        billed = int(m.group(1))
    else:
        m = re.search(r"Net\s*consumption\s*quantity\s*(\-?\d+)", t, re.IGNORECASE)
        if m:
            billed = int(m.group(1))

    # Monetary fields
    total = None
    m = re.search(r"Total\s*bill\s*value\s*([\d\.]+)", t, re.IGNORECASE)
    if m:
        total = parse_decimal_maybe(m.group(1))
    else:
        m = re.search(r"قيمة\s*الفاتورة\s*(\-?\d+)\s+(\d{3})", t)
        if m:
            din = int(m.group(1))
            fils = int(m.group(2))
            total = Decimal(din) + (Decimal(fils) / Decimal(1000))

    consumption_val = None
    m = re.search(r"قيم\s*الاستهلاك\s*([\d\.]+)", t)
    if m:
        consumption_val = parse_decimal_maybe(m.group(1))
    else:
        m = re.search(r"قيمة\s*الاستهلاك\s*(\-?\d+)\s+(\d{3})", t)
        if m:
            din = int(m.group(1))
            fils = int(m.group(2))
            consumption_val = Decimal(din) + (Decimal(fils) / Decimal(1000))

    fixed_sub = None
    m = re.search(r"(?:Fixed\s*subsidy\s*amount|قيمة\s*الخصم\s*الثابت)\s*([\-\d\.]+)", t, re.IGNORECASE)
    if m:
        fixed_sub = parse_decimal_maybe(m.group(1))

    network_fee = None
    m = re.search(r"(?:Network\s*services\s*fees|بدل\s*خدمات\s*الشبكة)\s*([\-\d\.]+)", t, re.IGNORECASE)
    if m:
        network_fee = parse_decimal_maybe(m.group(1))

    return ElectricityParsed(
        meter_number=meter,
        period_start=ps,
        period_end=pe,
        reading_date=rd,
        import_previous=imp_prev,
        import_current=imp_cur,
        export_previous=exp_prev,
        export_current=exp_cur,
        billed_kwh=billed,
        total_bill_value=total,
        consumption_value=consumption_val,
        network_services_fees=network_fee,
        fixed_subsidy_amount=fixed_sub,
    )
