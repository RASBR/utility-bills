# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class OcrResult:
    text: str
    engine: str
    confidence: Optional[float] = None


class OcrEngineError(RuntimeError):
    pass


def ocr_images_tesseract(image_paths: Iterable[str], lang: str = "ara+eng", psm: int = 6) -> OcrResult:
    """OCR images using Tesseract via pytesseract.

    Notes:
    - Requires `pytesseract` and OS-level tesseract installed.
    - For multiple images, we concatenate outputs separated by markers.
    """
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception as e:
        raise OcrEngineError("Tesseract OCR requested but dependencies are missing. Install optional extra: ocr_tesseract") from e

    parts = []
    for idx, p in enumerate(image_paths, start=1):
        img = Image.open(p)
        text = pytesseract.image_to_string(img, lang=lang, config=f"--psm {psm}")
        parts.append(f"\n\n--- IMAGE {idx} ---\n{text}")
    return OcrResult(text="".join(parts).strip(), engine="tesseract")


def ocr_images_paddle(image_paths: Iterable[str], lang: str = "ar") -> OcrResult:
    """OCR images using PaddleOCR.

    Notes:
    - Heavier dependency; best for structured tables (preserves boxes).
    - Here we return a flattened text output; callers can switch to box-based parsing later.
    """
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as e:
        raise OcrEngineError("PaddleOCR requested but dependency is missing. Install optional extra: ocr_paddle") from e

    # PaddleOCR language codes: 'ar' for Arabic, 'en' for English.
    ocr = PaddleOCR(use_angle_cls=True, lang=lang)
    lines = []
    for idx, p in enumerate(image_paths, start=1):
        result = ocr.ocr(p, cls=True)
        lines.append(f"\n\n--- IMAGE {idx} ---")
        for page in result:
            for item in page:
                txt = item[1][0]
                conf = float(item[1][1])
                lines.append(txt)
    return OcrResult(text="\n".join(lines).strip(), engine="paddleocr")
