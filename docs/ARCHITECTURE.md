# Architecture

This repository provides a reusable Django app that can be plugged into multiple projects (including projects using Django Allauth).

## Key goals

- Multi-user: each user has their own meters, bills, dashboard, and stats.
- Utility-agnostic dashboards: aggregation happens on a shared bill base table.
- Utility-specific details: electricity (solar / net-metering) and water details live in separate child tables.
- Two input methods:
  - OCR ingestion (Tesseract or PaddleOCR)
  - Manual entry (forms)
- Future: integrate into a “master dashboard” project by reusing the same app and models.

## Design principle

The system separates **physical energy movement** from **billing policy**:

- Physical readings:
  - Imported from grid readings (in/out meter channels)
  - Exported to grid readings (solar)
- Billing results:
  - Billed kWh (can be positive/zero/negative depending on policy)
  - Monetary totals (JOD)

We store readings and compute derived values (import_kwh/export_kwh/net_kwh) to keep data consistent.
