from django.urls import path
from .views import (
    member_dashboard,
    proceed_booking,
    capture_payment,
    create_booking,
    reports_dashboard
    dashboard
)

from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to Aquavaal Booking 🎣")

urlpatterns = [
    path("", home, name="home"),  # 👈 THIS FIXES YOUR ROOT URL

    path("dashboard/", member_dashboard, name="member_dashboard"),
    path("booking/<int:booking_id>/proceed/", proceed_booking),
    path("admin/capture-payment/<int:booking_id>/", capture_payment),
    path("create/", create_booking, name="create_booking"),
    path("reports/", reports_dashboard, name="reports"),
    path("", dashboard, name="dashboard"),
]
