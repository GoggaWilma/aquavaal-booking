from django.contrib import admin
from .models import Booking, BookingStand


class BookingStandInline(admin.TabularInline):
    model = BookingStand
    extra = 1
    fields = ("stand", "approval_status", "unavailable_reason", "is_active")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "display_booking_name",
        "stand_numbers",
        "user_membership_status",
        "booking_mode",
        "arrival_datetime",
        "departure_datetime",
        "status",
    )

    fields = (
        "user",
        "guest_name",
        "guest_email",
        "guest_phone",
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

    list_filter = (
        "booking_mode",
        "status",
        "payment_status",
        "attendance_status",
    )

    inlines = [BookingStandInline]

    def display_booking_name(self, obj):
        return obj.display_name()
    display_booking_name.short_description = "Guest / User"

    def user_membership_status(self, obj):
        if not obj.user:
            return "Guest"
        profile = getattr(obj.user, "profile", None)
        if not profile:
            return "No Profile"
        if profile.is_active_member():
            return "Active Member"
        return profile.membership_type
    user_membership_status.short_description = "Membership"

    def stand_numbers(self, obj):
        stands = obj.booking_stands.filter(stand__isnull=False).values_list("stand__number", flat=True)
        return ", ".join(str(number) for number in stands) if stands else "-"
    stand_numbers.short_description = "Stand Number"

@admin.register(BookingStand)
class BookingStandAdmin(admin.ModelAdmin):
    list_display = (
        "stand",
        "booking",
        "approval_status",
        "unavailable_reason",
        "is_active",
    )

    list_filter = (
        "approval_status",
        "is_active",
    )

    search_fields = (
        "stand__number",
        "booking__guest_name",
        "booking__user__email",
        "unavailable_reason",
    )
