# Data model

## Ownership

- A user owns one or more meters.
- A meter owns many bills.
- Bills are always filtered by the authenticated user in UI views.

## Tables

- `UtilityMeter`
  - user, utility_type, meter_number, nickname, location_note, is_active

- `UtilityBill` (base table)
  - user, meter, utility_type
  - period_start, period_end, reading_date, payment_date, issue_date
  - total_amount, currency
  - data_source (manual/ocr)
  - OCR audit fields (raw_ocr_text, ocr_engine, ocr_confidence, needs_review)

- `ElectricityBill` (child table)
  - import_previous/current
  - export_previous/current (optional)
  - billed_kwh (optional; can be negative for credit months)
  - optional monetary breakdown fields (consumption_value, network_services_fees, fixed_subsidy_amount)

- `WaterBill` (child table)
  - previous/current
  - billed_m3 (optional)

## Why this structure

- Shared analytics: run totals per month/year using `UtilityBill`.
- Detailed analytics: electricity solar import/export/net via `ElectricityBill`.
- Avoid duplicated schema for new utilities later.
