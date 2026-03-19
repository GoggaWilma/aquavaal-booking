from django.db import transaction
from bookings.models import Booking, BookingStand
from stands.models import Stand
from bookings.services.availability import check_stand_availability
from django.utils import timezone


def create_booking(
    user,
    stand_numbers,
    arrival,
    departure,
    booking_mode,
    member_count=0,
    non_member_adult_count=0,
    child_count=0,
):
    """
    Creates a booking with stand assignments after availability check.
    Returns booking object or raises Exception.
    """

    if arrival >= departure:
        raise Exception("Departure must be after arrival.")

    availability = check_stand_availability(
        stand_numbers,
        arrival,
        departure
    )

    if availability["blocked"]:
        raise Exception(f"These stands are already booked: {availability['blocked']}")

    with transaction.atomic():

        booking = Booking.objects.create(
            user=user,
            arrival_datetime=arrival,
            departure_datetime=departure,
            booking_mode=booking_mode,
            status="PENDING",
            payment_status="QUOTE",
            attendance_status="NOT_ARRIVED",
            member_count=member_count,
            non_member_adult_count=non_member_adult_count,
            child_count=child_count,
        )

        stands = Stand.objects.filter(number__in=stand_numbers)

        for stand in stands:
            BookingStand.objects.create(
                booking=booking,
                stand=stand
            )

    return booking
