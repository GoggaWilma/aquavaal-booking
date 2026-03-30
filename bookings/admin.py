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
        "user_membership_status",
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
        "member_count",
        "non_member_adult_count",
        "child_count",
        "total_days",
        "total_nights",
        "calculated_amount",
        "approved_amount",
        "override_note",
)
    

    list_filter = ("booking_mode", "status")
    inlines = [BookingStandInline]

    def user_membership_status(self, obj):
        profile = getattr(obj.user, "profile", None)
        if not profile:
            return "No Profile"
        if profile.is_active_member():
            return "Active Member"
        return profile.membership_type

    user_membership_status.short_description = "Membership"
