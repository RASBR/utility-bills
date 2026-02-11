# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django import forms
from django.core.exceptions import ValidationError

from .models import UtilityType


class DashboardFilterForm(forms.Form):
    utility_type = forms.ChoiceField(
        choices=[("", "All")] + list(UtilityType.choices),
        required=False
    )
    meter_id = forms.IntegerField(required=False)
    year = forms.IntegerField(required=False, min_value=2000, max_value=2100)


class MeterForm(forms.Form):
    utility_type = forms.ChoiceField(choices=UtilityType.choices)
    meter_number = forms.CharField(max_length=64)
    nickname = forms.CharField(max_length=64, required=False)
    location_note = forms.CharField(max_length=128, required=False)
    is_active = forms.BooleanField(required=False, initial=True)


class ElectricityManualBillForm(forms.Form):
    meter_id = forms.IntegerField()
    period_start = forms.DateField()
    period_end = forms.DateField()
    reading_date = forms.DateField(required=False)

    import_previous = forms.IntegerField(min_value=0)
    import_current = forms.IntegerField(min_value=0)

    export_previous = forms.IntegerField(min_value=0, required=False)
    export_current = forms.IntegerField(min_value=0, required=False)

    billed_kwh = forms.IntegerField(required=False)

    total_amount = forms.DecimalField(max_digits=12, decimal_places=3, required=False)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        import_prev = cleaned.get("import_previous")
        import_cur = cleaned.get("import_current")
        export_prev = cleaned.get("export_previous")
        export_cur = cleaned.get("export_current")

        if import_prev is not None and import_cur is not None:
            if import_cur < import_prev:
                raise ValidationError(
                    "Import current reading must be >= import previous reading."
                )

        if export_prev is not None and export_cur is not None:
            if export_cur < export_prev:
                raise ValidationError(
                    "Export current reading must be >= export previous reading."
                )

        return cleaned


class WaterManualBillForm(forms.Form):
    meter_id = forms.IntegerField()
    period_start = forms.DateField()
    period_end = forms.DateField()

    previous_reading = forms.IntegerField(min_value=0)
    current_reading = forms.IntegerField(min_value=0)
    billed_m3 = forms.IntegerField(required=False)

    total_amount = forms.DecimalField(max_digits=12, decimal_places=3, required=False)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        prev = cleaned.get("previous_reading")
        cur = cleaned.get("current_reading")

        if prev is not None and cur is not None:
            if cur < prev:
                raise ValidationError(
                    "Current reading must be >= previous reading."
                )

        return cleaned


class MultipleFileInput(forms.FileInput):
    """Custom widget that allows multiple file selection."""

    allow_multiple_selected = True

    def __init__(self, attrs: dict[str, Any] | None = None) -> None:
        default_attrs = {"multiple": True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class OcrUploadForm(forms.Form):
    utility_type = forms.ChoiceField(choices=UtilityType.choices)
    engine = forms.ChoiceField(choices=[("tesseract", "Tesseract"), ("paddleocr", "PaddleOCR")])
    images = forms.FileField(widget=MultipleFileInput(attrs={"accept": "image/*"}))


class OcrConfirmElectricityForm(forms.Form):
    """Form for confirming and saving OCR-parsed electricity bill data."""

    meter_number = forms.CharField(max_length=64)
    period_start = forms.DateField()
    period_end = forms.DateField()
    reading_date = forms.DateField(required=False)

    import_previous = forms.IntegerField(min_value=0)
    import_current = forms.IntegerField(min_value=0)

    export_previous = forms.IntegerField(min_value=0, required=False)
    export_current = forms.IntegerField(min_value=0, required=False)

    billed_kwh = forms.IntegerField(required=False)

    total_amount = forms.DecimalField(max_digits=12, decimal_places=3, required=False)
    consumption_value = forms.DecimalField(max_digits=12, decimal_places=3, required=False)
    network_services_fees = forms.DecimalField(max_digits=12, decimal_places=3, required=False)
    fixed_subsidy_amount = forms.DecimalField(max_digits=12, decimal_places=3, required=False)

    # Hidden fields for OCR metadata
    ocr_engine = forms.CharField(max_length=32, widget=forms.HiddenInput())
    raw_ocr_text = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        import_prev = cleaned.get("import_previous")
        import_cur = cleaned.get("import_current")
        export_prev = cleaned.get("export_previous")
        export_cur = cleaned.get("export_current")

        if import_prev is not None and import_cur is not None:
            if import_cur < import_prev:
                raise ValidationError(
                    "Import current reading must be >= import previous reading."
                )

        if export_prev is not None and export_cur is not None:
            if export_cur < export_prev:
                raise ValidationError(
                    "Export current reading must be >= export previous reading."
                )

        return cleaned

    def compute_needs_review(self, meter_found: bool) -> tuple[bool, list[str]]:
        """
        Determine if the bill needs manual review and return reasons.

        Returns:
            (needs_review, reasons) tuple
        """
        reasons: list[str] = []

        if not meter_found:
            reasons.append("Meter not found in user's registered meters")

        # Check billed_kwh vs computed net_kwh
        import_prev = self.cleaned_data.get("import_previous")
        import_cur = self.cleaned_data.get("import_current")
        export_prev = self.cleaned_data.get("export_previous")
        export_cur = self.cleaned_data.get("export_current")
        billed_kwh = self.cleaned_data.get("billed_kwh")

        if import_prev is not None and import_cur is not None:
            import_kwh = import_cur - import_prev
            export_kwh = 0
            if export_prev is not None and export_cur is not None:
                export_kwh = export_cur - export_prev
            computed_net = import_kwh - export_kwh

            if billed_kwh is not None and billed_kwh != computed_net:
                reasons.append(
                    f"Billed kWh ({billed_kwh}) != computed net kWh ({computed_net})"
                )

        return (len(reasons) > 0, reasons)
