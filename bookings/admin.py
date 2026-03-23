from django.contrib import admin
from .models import Booking, BookingStand


class BookingStandInline(admin.TabularInline):
    model = BookingStand
    extra = 1  # shows empty row to add stands


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "payment_status",
        "attendance_status",
        "arrival_datetime",
    )

    inlines = [BookingStandInline]
