# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class UtilityType(models.TextChoices):
    ELECTRICITY = "electricity", "Electricity"
    WATER = "water", "Water"


class DataSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    OCR = "ocr", "OCR"


class Currency(models.TextChoices):
    JOD = "JOD", "JOD"


class UtilityMeter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="utility_meters")
    utility_type = models.CharField(max_length=32, choices=UtilityType.choices)
    meter_number = models.CharField(max_length=64)
    nickname = models.CharField(max_length=64, blank=True, default="")
    location_note = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (("user", "utility_type", "meter_number"),)
        indexes = [
            models.Index(fields=["user", "utility_type"]),
            models.Index(fields=["meter_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.utility_type}:{self.meter_number}"


class UtilityBill(models.Model):
    """Base bill record used for dashboards and aggregation.

    Child tables (multi-table inheritance):
    - ElectricityBill
    - WaterBill
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="utility_bills")
    meter = models.ForeignKey(UtilityMeter, on_delete=models.PROTECT, related_name="bills")
    utility_type = models.CharField(max_length=32, choices=UtilityType.choices)

    period_start = models.DateField()
    period_end = models.DateField()
    issue_date = models.DateField(null=True, blank=True)
    reading_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)

    total_amount = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0.000"))
    currency = models.CharField(max_length=8, choices=Currency.choices, default=Currency.JOD)

    data_source = models.CharField(max_length=16, choices=DataSource.choices, default=DataSource.MANUAL)

    # OCR audit
    ocr_engine = models.CharField(max_length=32, blank=True, default="")
    ocr_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    raw_ocr_text = models.TextField(blank=True, default="")
    needs_review = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["user", "utility_type"]),
            models.Index(fields=["meter", "period_end"]),
            models.Index(fields=["period_end"]),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(total_amount__gte=Decimal("-999999999.999")), name="ub_total_amount_reasonable"),
        ]

    def clean(self) -> None:
        """Validate utility_type matches meter's utility_type."""
        if self.meter_id and self.utility_type and self.meter.utility_type != self.utility_type:
            raise ValidationError(
                {"utility_type": "UtilityBill.utility_type must match UtilityMeter.utility_type"}
            )

    def __str__(self) -> str:
        return f"{self.utility_type}:{self.meter.meter_number}:{self.period_start}->{self.period_end}"


class ElectricityBill(models.Model):
    bill = models.OneToOneField(UtilityBill, on_delete=models.CASCADE, related_name="electricity")

    import_previous = models.IntegerField()
    import_current = models.IntegerField()

    export_previous = models.IntegerField(null=True, blank=True)
    export_current = models.IntegerField(null=True, blank=True)

    billed_kwh = models.IntegerField(null=True, blank=True)  # can be negative depending on policy

    # Optional monetary breakdown fields (JOD)
    consumption_value = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    network_services_fees = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    fixed_subsidy_amount = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["billed_kwh"]),
        ]

    def clean(self) -> None:
        """Validate meter readings are consistent."""
        errors: dict[str, str] = {}

        # import_current must be >= import_previous
        if self.import_current < self.import_previous:
            errors["import_current"] = "Import current reading must be >= import previous reading."

        # export_current must be >= export_previous if both are set
        if self.export_current is not None and self.export_previous is not None:
            if self.export_current < self.export_previous:
                errors["export_current"] = "Export current reading must be >= export previous reading."

        if errors:
            raise ValidationError(errors)

    @property
    def import_kwh(self) -> int:
        return int(self.import_current) - int(self.import_previous)

    @property
    def export_kwh(self) -> int:
        if self.export_current is None or self.export_previous is None:
            return 0
        return int(self.export_current) - int(self.export_previous)

    @property
    def net_kwh(self) -> int:
        return self.import_kwh - self.export_kwh

    @property
    def billed_kwh_mismatch(self) -> bool:
        """Check if billed_kwh differs from computed net_kwh (potential data issue)."""
        if self.billed_kwh is None:
            return False
        return self.billed_kwh != self.net_kwh

    def __str__(self) -> str:
        return f"ElectricityBill({self.bill_id})"


class WaterBill(models.Model):
    bill = models.OneToOneField(UtilityBill, on_delete=models.CASCADE, related_name="water")

    previous_reading = models.IntegerField()
    current_reading = models.IntegerField()
    billed_m3 = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["billed_m3"]),
        ]

    def clean(self) -> None:
        """Validate water meter readings are consistent."""
        if self.current_reading < self.previous_reading:
            raise ValidationError(
                {"current_reading": "Current reading must be >= previous reading."}
            )

    @property
    def consumption_m3(self) -> int:
        return int(self.current_reading) - int(self.previous_reading)

    def __str__(self) -> str:
        return f"WaterBill({self.bill_id})"
