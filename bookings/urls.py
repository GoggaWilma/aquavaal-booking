from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("report/stands/", views.stand_report_pdf, name="stand_report"),
]
