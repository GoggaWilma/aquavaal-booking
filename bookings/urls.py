from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("reports/", views.reports_dashboard, name="reports"),

    path("dashboard/", views.member_dashboard, name="member_dashboard"),
    path("booking/<int:booking_id>/proceed/", views.proceed_booking),
    path("admin/capture-payment/<int:booking_id>/", views.capture_payment),
    path("create/", views.create_booking, name="create_booking"),
    path("report/stands/", views.stand_report_pdf, name="stand_report"),
]

from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to Aqua Vaal Hengelklub 🎣")

