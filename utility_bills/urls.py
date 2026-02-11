# 2026-02-11 07:39 
# https://chat.openai.com/

from django.urls import path
from . import views

app_name = "utility_bills"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("meters/", views.meters_list, name="meters_list"),
    path("meters/add/", views.meter_add, name="meter_add"),
    path("bills/add/", views.bill_add, name="bill_add"),
    path("bills/<int:bill_id>/", views.bill_detail, name="bill_detail"),
    path("ocr/upload/", views.ocr_upload, name="ocr_upload"),
    path("ocr/save/", views.ocr_save, name="ocr_save"),
]
