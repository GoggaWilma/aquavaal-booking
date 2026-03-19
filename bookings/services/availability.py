from bookings.models import BookingStand

BLOCKING_STATUSES = ['PENDING', 'PARTIAL', 'APPROVED']


def check_stand_availability(stand_ids, start_datetime, end_datetime):

    blocked = []
    available = []

    for stand_id in stand_ids:

        conflicts = BookingStand.objects.filter(
            stand_id=stand_id,
            booking__status__in=BLOCKING_STATUSES,
            booking__arrival_datetime__lt=end_datetime,
            booking__departure_datetime__gt=start_datetime,
            is_active=True,
        )

        if conflicts.exists():
            conflict = conflicts.first()
            blocked.append({
                "stand_id": stand_id,
                "booking_id": conflict.booking.id
            })
        else:
            available.append(stand_id)

    return {
        "available": available,
        "blocked": blocked
    }
