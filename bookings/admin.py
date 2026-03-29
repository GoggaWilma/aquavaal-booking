from django.contrib import admin
from django import forms
from .models import Booking, BookingStand


class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = "__all__"


class BookingStandInline(admin.TabularInline):
    model = BookingStand
    extra = 1


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm

    list_display = (
        "id",
        "user",
        "booking_mode",
        "payment_status",
        "attendance_status",
        "arrival_datetime",
        "departure_datetime",
        "status",
    )

    fields = (
        "user",
        "booking_mode",
        "arrival_datetime",
        "departure_datetime",
        "status",
        "payment_status",
        "attendance_status",
    )

    list_filter = ("booking_mode", "status")
    inlines = [BookingStandInline]
