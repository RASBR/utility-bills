# utility-bills

Reusable Django app for **utility bills** with:
- Electricity (supports **solar / net-metering**: import from grid, export to grid, net billed/credit)
- Water (ready structure)
- **OCR ingestion** (Tesseract via `pytesseract`, optional PaddleOCR)
- **Manual entry** (same models)
- Multi-user dashboards: stats per **utility / meter / month / year** with filters and charts

## Install (development / editable)

```powershell
pip install -e D:\03_sbr-utility-bills\utility-bills
```

Optional OCR dependencies:

```powershell
pip install -e ".[ocr_tesseract]"
# or (heavier)
pip install -e ".[ocr_paddle]"
```

## Integrate into an existing Django project (including Allauth)

1. Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS += [
    "utility_bills",
]
```

2. Include URLs:

```python
from django.urls import include, path

urlpatterns += [
    path("utilities/", include("utility_bills.urls")),
]
```

3. Run migrations:

```powershell
python manage.py makemigrations utility_bills
python manage.py migrate
```

> This app **does not create** any auth/allauth tables. It references the project user model via `settings.AUTH_USER_MODEL`.

## Quick start URLs

- Dashboard: `/utilities/`
- Add bill manually: `/utilities/bills/add/`
- OCR upload (multi-image): `/utilities/ocr/upload/`
- Meters: `/utilities/meters/`

## Documentation
See `docs/`:
- `ARCHITECTURE.md`
- `DATA_MODEL.md`
- `OCR_FLOW.md`
- `SOLAR_NET_METERING.md`
- `DASHBOARD_STATS.md`
- `INTEGRATION.md`
