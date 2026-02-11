# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

from decimal import Decimal
from typing import Optional


ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
WESTERN_DIGITS = "0123456789"
_DIGIT_TRANS = str.maketrans(ARABIC_DIGITS, WESTERN_DIGITS)


def normalize_digits(text: str) -> str:
    return (text or "").translate(_DIGIT_TRANS)


def parse_decimal_maybe(value: str) -> Optional[Decimal]:
    if value is None:
        return None
    v = value.strip().replace(",", "")
    if not v:
        return None
    try:
        return Decimal(v)
    except Exception:
        return None
