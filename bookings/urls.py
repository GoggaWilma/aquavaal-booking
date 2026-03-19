from django.urls import path
from .views import member_dashboard, proceed_booking, capture_payment, create_booking, test_view

urlpatterns = [
    path("dashboard/", member_dashboard, name="member_dashboard"),
    path("booking/<int:booking_id>/proceed/", proceed_booking, name="proceed_booking"),
    path("admin/capture-payment/<int:booking_id>/", capture_payment, name="capture_payment"),
    path("create/", create_booking, name="create_booking"),
    path("test/", test_view), 
]
