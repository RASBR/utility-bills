# 2026-02-11 07:39 
# https://chat.openai.com/

from __future__ import annotations

import json
import tempfile
from datetime import date
from decimal import Decimal
from typing import Any

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    DashboardFilterForm,
    ElectricityManualBillForm,
    MeterForm,
    OcrConfirmElectricityForm,
    OcrUploadForm,
    WaterManualBillForm,
)
from .models import (
    DataSource,
    ElectricityBill,
    UtilityBill,
    UtilityMeter,
    UtilityType,
    WaterBill,
)
from .parsers.electricity_parser import parse_electricity_text
from .services.classifiers import classify_layout
from .services.ocr_engine import ocr_images_paddle, ocr_images_tesseract


def _year_default() -> int:
    return date.today().year


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    form = DashboardFilterForm(request.GET or None)
    form.is_valid()

    utility_type = form.cleaned_data.get("utility_type") if form.cleaned_data else ""
    meter_id = form.cleaned_data.get("meter_id") if form.cleaned_data else None
    year = form.cleaned_data.get("year") if form.cleaned_data else None
    if not year:
        year = _year_default()

    qs = UtilityBill.objects.filter(user=request.user, period_end__year=year)
    if utility_type:
        qs = qs.filter(utility_type=utility_type)
    if meter_id:
        qs = qs.filter(meter_id=meter_id)

    total_spent = qs.aggregate(s=Sum("total_amount"))["s"] or Decimal("0.000")

    # Chart: monthly totals (simple)
    monthly = []
    for m in range(1, 13):
        msum = qs.filter(period_end__month=m).aggregate(s=Sum("total_amount"))["s"] or Decimal("0.000")
        monthly.append(float(msum))

    # Chart: electricity net kWh by month (if present)
    elec_net = [0] * 12
    elec_import = [0] * 12
    elec_export = [0] * 12
    elec_billed = [0] * 12
    elec_bills = ElectricityBill.objects.filter(bill__in=qs.filter(utility_type=UtilityType.ELECTRICITY)).select_related("bill")
    for eb in elec_bills:
        idx = eb.bill.period_end.month - 1
        elec_import[idx] += eb.import_kwh
        elec_export[idx] += eb.export_kwh
        elec_net[idx] += eb.net_kwh
        if eb.billed_kwh is not None:
            elec_billed[idx] += int(eb.billed_kwh)

    chart_payload = {
        "labels": [f"{year}-{m:02d}" for m in range(1, 13)],
        "monthly_total_amount": monthly,
        "electricity_import_kwh": elec_import,
        "electricity_export_kwh": elec_export,
        "electricity_net_kwh": elec_net,
        "electricity_billed_kwh": elec_billed,
    }

    meters = UtilityMeter.objects.filter(user=request.user, is_active=True).order_by("utility_type", "meter_number")

    # Latest bills list (simple)
    latest_bills = qs.select_related("meter").order_by("-period_end")[:20]

    return render(
        request,
        "utility_bills/dashboard.html",
        {
            "form": form,
            "total_spent": total_spent,
            "meters": meters,
            "latest_bills": latest_bills,
            "chart_payload_json": json.dumps(chart_payload),
            "year": year,
        },
    )


@login_required
def meters_list(request: HttpRequest) -> HttpResponse:
    meters = UtilityMeter.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "utility_bills/meters_list.html", {"meters": meters})


@login_required
def meter_add(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = MeterForm(request.POST)
        if form.is_valid():
            UtilityMeter.objects.create(
                user=request.user,
                utility_type=form.cleaned_data["utility_type"],
                meter_number=form.cleaned_data["meter_number"],
                nickname=form.cleaned_data.get("nickname") or "",
                location_note=form.cleaned_data.get("location_note") or "",
                is_active=bool(form.cleaned_data.get("is_active")),
            )
            return redirect(reverse("utility_bills:meters_list"))
    else:
        form = MeterForm()
    return render(request, "utility_bills/meter_add.html", {"form": form})


@login_required
def bill_add(request: HttpRequest) -> HttpResponse:
    utility_type = request.GET.get("utility_type") or UtilityType.ELECTRICITY
    if request.method == "POST":
        if utility_type == UtilityType.WATER:
            form = WaterManualBillForm(request.POST)
            if form.is_valid():
                meter = get_object_or_404(UtilityMeter, id=form.cleaned_data["meter_id"], user=request.user)
                bill = UtilityBill.objects.create(
                    user=request.user,
                    meter=meter,
                    utility_type=UtilityType.WATER,
                    period_start=form.cleaned_data["period_start"],
                    period_end=form.cleaned_data["period_end"],
                    total_amount=form.cleaned_data.get("total_amount") or Decimal("0.000"),
                    data_source=DataSource.MANUAL,
                )
                WaterBill.objects.create(
                    bill=bill,
                    previous_reading=form.cleaned_data["previous_reading"],
                    current_reading=form.cleaned_data["current_reading"],
                    billed_m3=form.cleaned_data.get("billed_m3"),
                )
                return redirect(reverse("utility_bills:bill_detail", kwargs={"bill_id": bill.id}))
        else:
            form = ElectricityManualBillForm(request.POST)
            if form.is_valid():
                meter = get_object_or_404(UtilityMeter, id=form.cleaned_data["meter_id"], user=request.user)
                bill = UtilityBill.objects.create(
                    user=request.user,
                    meter=meter,
                    utility_type=UtilityType.ELECTRICITY,
                    period_start=form.cleaned_data["period_start"],
                    period_end=form.cleaned_data["period_end"],
                    reading_date=form.cleaned_data.get("reading_date"),
                    total_amount=form.cleaned_data.get("total_amount") or Decimal("0.000"),
                    data_source=DataSource.MANUAL,
                )
                ElectricityBill.objects.create(
                    bill=bill,
                    import_previous=form.cleaned_data["import_previous"],
                    import_current=form.cleaned_data["import_current"],
                    export_previous=form.cleaned_data.get("export_previous"),
                    export_current=form.cleaned_data.get("export_current"),
                    billed_kwh=form.cleaned_data.get("billed_kwh"),
                )
                return redirect(reverse("utility_bills:bill_detail", kwargs={"bill_id": bill.id}))
    else:
        if utility_type == UtilityType.WATER:
            form = WaterManualBillForm()
        else:
            form = ElectricityManualBillForm()

    meters = UtilityMeter.objects.filter(user=request.user, utility_type=utility_type, is_active=True).order_by("meter_number")
    return render(request, "utility_bills/bill_add.html", {"form": form, "utility_type": utility_type, "meters": meters})


@login_required
def bill_detail(request: HttpRequest, bill_id: int) -> HttpResponse:
    bill = get_object_or_404(UtilityBill.objects.select_related("meter"), id=bill_id, user=request.user)
    return render(request, "utility_bills/bill_detail.html", {"bill": bill})


@login_required
def ocr_upload(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = OcrUploadForm(request.POST, request.FILES)
        if form.is_valid():
            utility_type = form.cleaned_data["utility_type"]
            engine = form.cleaned_data["engine"]
            files = request.FILES.getlist("images")

            # Save uploads temporarily
            tmpdir = tempfile.mkdtemp(prefix="ub_ocr_")
            paths: list[str] = []
            for f in files:
                p = tmpdir + "/" + f.name
                with open(p, "wb") as out:
                    for chunk in f.chunks():
                        out.write(chunk)
                paths.append(p)

            if engine == "paddleocr":
                ocr_res = ocr_images_paddle(paths, lang="ar" if utility_type == UtilityType.ELECTRICITY else "en")
            else:
                ocr_res = ocr_images_tesseract(paths, lang="ara+eng", psm=6)

            layout = classify_layout(ocr_res.text)

            # Parse and prepare confirmation form
            parsed = None
            confirm_form = None
            if utility_type == UtilityType.ELECTRICITY:
                parsed = parse_electricity_text(ocr_res.text)
                # Pre-populate confirmation form with parsed values
                initial_data: dict[str, Any] = {
                    "meter_number": parsed.meter_number or "",
                    "period_start": parsed.period_start,
                    "period_end": parsed.period_end,
                    "reading_date": parsed.reading_date,
                    "import_previous": parsed.import_previous,
                    "import_current": parsed.import_current,
                    "export_previous": parsed.export_previous,
                    "export_current": parsed.export_current,
                    "billed_kwh": parsed.billed_kwh,
                    "total_amount": parsed.total_bill_value,
                    "consumption_value": parsed.consumption_value,
                    "network_services_fees": parsed.network_services_fees,
                    "fixed_subsidy_amount": parsed.fixed_subsidy_amount,
                    "ocr_engine": ocr_res.engine,
                    "raw_ocr_text": ocr_res.text,
                }
                confirm_form = OcrConfirmElectricityForm(initial=initial_data)

            return render(
                request,
                "utility_bills/ocr_result.html",
                {
                    "form": form,
                    "ocr_text": ocr_res.text,
                    "engine": ocr_res.engine,
                    "layout": layout,
                    "parsed": parsed,
                    "confirm_form": confirm_form,
                    "utility_type": utility_type,
                },
            )
    else:
        form = OcrUploadForm()

    return render(request, "utility_bills/ocr_upload.html", {"form": form})


@login_required
def ocr_save(request: HttpRequest) -> HttpResponse:
    """Save OCR-parsed electricity bill after user confirmation."""
    if request.method != "POST":
        return redirect(reverse("utility_bills:ocr_upload"))

    form = OcrConfirmElectricityForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "utility_bills/ocr_result.html",
            {
                "confirm_form": form,
                "utility_type": UtilityType.ELECTRICITY,
                "errors": form.errors,
            },
        )

    # Look up meter by meter_number for this user
    meter_number = form.cleaned_data["meter_number"]
    try:
        meter = UtilityMeter.objects.get(
            user=request.user,
            utility_type=UtilityType.ELECTRICITY,
            meter_number=meter_number,
        )
        meter_found = True
    except UtilityMeter.DoesNotExist:
        # Return error - do NOT auto-create meter
        return render(
            request,
            "utility_bills/ocr_result.html",
            {
                "confirm_form": form,
                "utility_type": UtilityType.ELECTRICITY,
                "meter_error": f"Meter '{meter_number}' not found. Please add this meter first.",
            },
        )

    # Compute needs_review flag
    needs_review, review_reasons = form.compute_needs_review(meter_found=meter_found)

    # Create UtilityBill
    bill = UtilityBill.objects.create(
        user=request.user,
        meter=meter,
        utility_type=UtilityType.ELECTRICITY,
        period_start=form.cleaned_data["period_start"],
        period_end=form.cleaned_data["period_end"],
        reading_date=form.cleaned_data.get("reading_date"),
        total_amount=form.cleaned_data.get("total_amount") or Decimal("0.000"),
        data_source=DataSource.OCR,
        ocr_engine=form.cleaned_data.get("ocr_engine", ""),
        raw_ocr_text=form.cleaned_data.get("raw_ocr_text", ""),
        needs_review=needs_review,
    )

    # Create ElectricityBill
    ElectricityBill.objects.create(
        bill=bill,
        import_previous=form.cleaned_data["import_previous"],
        import_current=form.cleaned_data["import_current"],
        export_previous=form.cleaned_data.get("export_previous"),
        export_current=form.cleaned_data.get("export_current"),
        billed_kwh=form.cleaned_data.get("billed_kwh"),
        consumption_value=form.cleaned_data.get("consumption_value"),
        network_services_fees=form.cleaned_data.get("network_services_fees"),
        fixed_subsidy_amount=form.cleaned_data.get("fixed_subsidy_amount"),
    )

    return redirect(reverse("utility_bills:bill_detail", kwargs={"bill_id": bill.id}))
