from django.db import models
from django.conf import settings

# -------------------------
# BOOKING MODEL
# -------------------------

class Booking(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    arrival_datetime = models.DateTimeField()
    departure_datetime = models.DateTimeField()

    booking_mode = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default="PENDING")
    payment_status = models.CharField(max_length=50, default="UNPAID")
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

    def proceed_with_approved_stands(self):
        if self.is_locked():
            return

        for stand in self.booking_stands.filter(
            approval_status="REJECTED",
            is_active=True
        ):
            stand.is_active = False
            stand.save(update_fields=["is_active"])

        self.recalculate_status()
        self.recalculate_financials()

        self.status = "READY_FOR_GATE"
        self.save(update_fields=["status"])

    def recalculate_status(self):
        stands = self.booking_stands.all()

        if not stands.exists():
            return

        approved_count = stands.filter(approval_status="APPROVED").count()
        rejected_count = stands.filter(approval_status="REJECTED").count()
        total = stands.count()

        if approved_count == 0 and rejected_count == total:
            self.status = "REJECTED"
        elif approved_count > 0 and rejected_count > 0:
            self.status = "PARTIAL"
        elif approved_count == total:
            self.status = "APPROVED"
        else:
            self.status = "PENDING"

        self.save(update_fields=["status"])
        self.lock_financials_if_final()

    def recalculate_financials(self):
        active_stands = self.booking_stands.filter(is_active=True)

        stand_count = active_stands.count()

        if stand_count == 0:
            self.calculated_amount = 0
            self.save(update_fields=["calculated_amount"])
            return

        DAY_RATE = 80
        NIGHT_RATE = 40
        payable_adults = self.non_member_adult_count

        total = payable_adults * (
            self.total_days * DAY_RATE +
            self.total_nights * NIGHT_RATE
        )

        self.calculated_amount = total
        self.save(update_fields=["calculated_amount"])

    def lock_financials_if_final(self):
        if self.attendance_status == "FINAL":
            self.approved_amount = self.calculated_amount
            self.save(update_fields=["approved_amount"])

    def is_locked(self):
        return self.attendance_status == "FINAL"

    def save(self, *args, **kwargs):
        super().save
        if self.attendance_status == "FINAL" and self.approved_amount is None:
            self.approved_amount = self.calculated_amount
            super().save(update_fields=["approved_amount"])
        else:
            (*args, **kwargs)
        
# -------------------------
# BOOKING STAND MODEL
# -------------------------

APPROVAL_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("APPROVED", "Approved"),
    ("PARTIALLY_APPROVED", "Partially Approved"),
    ("AWAITING_MEMBER_ACTION", "Awaiting Member Action"),
    ("REJECTED", "Rejected"),
    ("READY_FOR_GATE", "Ready For Gate"),
    ("OVERRIDDEN", "Overridden"),
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
        related_name="stand_bookings"
    )

    approval_status = models.CharField(
        max_length=30,
        choices=APPROVAL_STATUS_CHOICES,
        default="PENDING"
    )

    is_active = models.BooleanField(default=True)

    action_timestamp = models.DateTimeField(null=True, blank=True)

    approval_status = models.CharField(
        max_length=30,
        choices=APPROVAL_STATUS_CHOICES,
        default="PENDING"
    )

    is_active = models.BooleanField(default=True)

    action_timestamp = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)

    def __str__(self):
        return f"Stand {self.stand.number} - {self.approval_status}"

class BookingStandAudit(models.Model):
    booking_stand = models.ForeignKey(
        "bookings.BookingStand",
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
    if self.booking_stand and self.booking_stand.stand:
        stand_number = self.booking_stand.stand.number
    else:
        stand_number = "Unknown"

    return f"Stand {stand_number} {self.old_status} → {self.new_status}"
