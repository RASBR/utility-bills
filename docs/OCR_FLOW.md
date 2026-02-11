# OCR flow

## Supported engines

- Tesseract via `pytesseract`
  - Lightweight
  - Good for summary screenshots (label → value)
  - Table structure may collapse

- PaddleOCR (optional)
  - Heavier dependency
  - Better for structured tables (preserves layout via boxes)
  - Useful for official bills with dinar/fils columns and import/export blocks

## Batch OCR

Multiple images are supported in one upload. The engine concatenates OCR outputs with markers:

- `--- IMAGE 1 ---`
- `--- IMAGE 2 ---`
- ...

This allows:
- multi-page bills
- multiple screenshots for same billing period

## Parsing strategy

1. Normalize digits (Arabic-Indic → Western)
2. Classify layout using lightweight heuristics
3. Route to a utility-specific parser
4. Produce a normalized parsed object for preview and saving

The app currently renders parsed previews; a save pipeline can be added next.
