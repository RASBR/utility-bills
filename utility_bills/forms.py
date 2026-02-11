# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

from django import forms
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


class WaterManualBillForm(forms.Form):
    meter_id = forms.IntegerField()
    period_start = forms.DateField()
    period_end = forms.DateField()

    previous_reading = forms.IntegerField(min_value=0)
    current_reading = forms.IntegerField(min_value=0)
    billed_m3 = forms.IntegerField(required=False)

    total_amount = forms.DecimalField(max_digits=12, decimal_places=3, required=False)


class OcrUploadForm(forms.Form):
    utility_type = forms.ChoiceField(choices=UtilityType.choices)
    engine = forms.ChoiceField(choices=[("tesseract", "Tesseract"), ("paddleocr", "PaddleOCR")])
    images = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))
