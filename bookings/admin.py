from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Booking, BookingStand

class BookingStandInline(admin.TabularInline):
    model = BookingStand
    extra = 0

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
   inlines = [BookingStandInline]

   list_display = (
       'id',
       'user',
       'status',
       'payment_status',
       'attendance_status',
       'arrival_datetime',
       'departure_datetime',
       'capture_payment_button',
   )

   def capture_payment_button(self, obj):
       if obj.attendance_status != "FINAL":
           url = reverse("capture_payment", args=[obj.id])
           return format_html(
               '<a class="button" href="{}">Mark Payment Captured</a>', url
           )
       return "Finalized"

   capture_payment_button.short_description = "Capture Payment"

   list_filter = ('status', 'payment_status', 'attendance_status')
   inlines = [BookingStandInline]


@admin.register(BookingStand)
class BookingStandAdmin(admin.ModelAdmin):
    list_display = ("booking", "stand", "approval_status", "is_active")

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
