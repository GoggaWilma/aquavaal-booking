from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("report/stands/", views.stand_report_pdf, name="stand_report"),
    path("booking-stand-action/", views.booking_stand_action, name="booking_stand_action"),
]
