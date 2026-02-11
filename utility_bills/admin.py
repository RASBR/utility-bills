# 2026-02-11 07:39 
# https://chat.openai.com/

from django.contrib import admin
from .models import UtilityMeter, UtilityBill, ElectricityBill, WaterBill


@admin.register(UtilityMeter)
class UtilityMeterAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "utility_type", "meter_number", "nickname", "is_active", "created_at")
    list_filter = ("utility_type", "is_active")
    search_fields = ("meter_number", "nickname", "user__username", "user__email")


@admin.register(UtilityBill)
class UtilityBillAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "utility_type", "meter", "period_start", "period_end", "total_amount", "currency", "data_source")
    list_filter = ("utility_type", "data_source", "currency")
    search_fields = ("meter__meter_number", "user__username", "user__email")
    date_hierarchy = "period_end"


@admin.register(ElectricityBill)
class ElectricityBillAdmin(admin.ModelAdmin):
    list_display = ("id", "bill", "import_kwh", "export_kwh", "net_kwh", "billed_kwh")
    search_fields = ("bill__meter__meter_number",)


@admin.register(WaterBill)
class WaterBillAdmin(admin.ModelAdmin):
    list_display = ("id", "bill", "billed_m3")
    search_fields = ("bill__meter__meter_number",)
