from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError

User = get_user_model()

# -------------------------
# BOOKING MODEL
# -------------------------

BOOKING_MODE_CHOICES = [
    ("ADMIN", "Admin Captured"),
    ("REQUEST", "Member Request"),
    ("WALKIN", "Walk-in"),
]

class Booking(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    guest_name = models.CharField(max_length=150, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    guest_phone = models.CharField(max_length=30, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    arrival_datetime = models.DateTimeField()
    departure_datetime = models.DateTimeField()

    booking_mode = models.CharField(
        max_length=20,
        choices=BOOKING_MODE_CHOICES,
        default="ADMIN"
    )

    status = models.CharField(max_length=50, default="PENDING")
    payment_status = models.CharField(max_length=50, default="PENDING")
    attendance_status = models.CharField(max_length=50, default="PENDING")

    member_count = models.PositiveIntegerField(default=0)
    non_member_adult_count = models.PositiveIntegerField(default=0)
    child_count = models.PositiveIntegerField(default=0)

    total_days = models.PositiveIntegerField(default=0)
    total_nights = models.PositiveIntegerField(default=0)

    calculated_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    override_note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Booking {self.id}"

    def display_name(self):
        if self.user:
            return self.user.get_full_name().strip() or self.user.email
        return self.guest_name or "Guest"

    def is_locked(self):
        return self.attendance_status == "FINAL"

    def user_profile(self):
        if not self.user:
            return None
        return getattr(self.user, "profile", None)

    def booking_user_is_active_member(self):
        profile = self.user_profile()
        if not profile:
            return False
        return profile.is_active_member()

    def booking_user_membership_type(self):
        profile = self.user_profile()
        if not profile:
            return "GUEST"
        return profile.membership_type

    def clean(self):
        if self.departure_datetime <= self.arrival_datetime:
            raise ValidationError("Departure must be after arrival.")

        if not self.user and not self.guest_name:
            raise ValidationError("Provide either a linked user or a guest name.")

    def recalculate_financials(self):
        DAY_RATE = 80
        NIGHT_RATE = 40

        payable_guests = self.non_member_adult_count

        if not self.booking_user_is_active_member():
            payable_guests += 1

        total_per_person = (
            self.total_days * DAY_RATE +
            self.total_nights * NIGHT_RATE
        )

        total = payable_guests * total_per_person

        self.calculated_amount = total
        self.save(update_fields=["calculated_amount"])

    def lock_financials_if_final(self):
        if self.attendance_status == "FINAL":
            self.approved_amount = self.calculated_amount
            self.save(update_fields=["approved_amount"])

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        if self.attendance_status == "FINAL" and self.approved_amount is None:
            self.approved_amount = self.calculated_amount
            super().save(update_fields=["approved_amount"])


#--------------------------
# BOOKING STAND MODEL
# -------------------------

APPROVAL_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
    ("READY_FOR_GATE", "Ready For Gate"),
]

class BookingStand(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="booking_stands"
    )

    stand = models.ForeignKey(
        "stands.Stand",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    approval_status = models.CharField(
        max_length=30,
        choices=APPROVAL_STATUS_CHOICES,
        default="PENDING"
    )

    is_active = models.BooleanField(default=True)

    action_timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        stand_label = self.stand.number if self.stand else "No Stand"
        return f"Stand {stand_label} - {self.approval_status}"

    def clean(self):
        if not self.stand or not self.booking:
            return

        overlapping = BookingStand.objects.filter(
            stand=self.stand,
            booking__arrival_datetime__lt=self.booking.departure_datetime,
            booking__departure_datetime__gt=self.booking.arrival_datetime,
        ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError(f"Stand {self.stand.number} is already booked for this period.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# -------------------------
# AUDIT MODEL
# -------------------------

class BookingStandAudit(models.Model):
    booking_stand = models.ForeignKey(
        BookingStand,
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.old_status} → {self.new_status}"
