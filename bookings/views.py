from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from stands.models import Stand
from .models import Booking, BookingStand
from .forms import DashboardBookingForm


@login_required
def dashboard(request):
    today = timezone.now().date()
    user_bookings = Booking.objects.filter(user=request.user).order_by("-created_at")[:10]

    selected_arrival = None
    selected_departure = None
    available_stands = Stand.objects.none()
    booked_stands = []

    if request.method == "POST":
        action = request.POST.get("action")

        # STEP 1: Check availability
        if action == "check":
            temp_form = DashboardBookingForm(request.POST)

            if temp_form.is_valid():
                selected_arrival = temp_form.cleaned_data["arrival_date"]
                selected_departure = temp_form.cleaned_data["departure_date"]

                arrival_dt = datetime.combine(selected_arrival, time(12, 0))
                departure_dt = datetime.combine(selected_departure, time(12, 0))

                if departure_dt <= arrival_dt:
                    messages.error(request, "Departure date must be after arrival date.")
                    booking_form = DashboardBookingForm(request.POST, available_stands=Stand.objects.none())
                else:
                    overlapping = BookingStand.objects.filter(
                        is_active=True,
                        booking__arrival_datetime__lt=departure_dt,
                        booking__departure_datetime__gt=arrival_dt,
                    ).select_related("stand", "booking", "booking__user")

                    booked_stand_ids = set()
                    booked_stands = []

                    for bs in overlapping:
                        if bs.stand_id and bs.stand_id not in booked_stand_ids:
                            booked_stand_ids.add(bs.stand_id)
                            booked_stands.append({
                                "number": bs.stand.number,
                                "name": bs.booking.user.get_full_name().strip() or bs.booking.user.email,
                            })

                    available_stands = Stand.objects.exclude(id__in=booked_stand_ids).order_by("number")
                    booked_stands = sorted(booked_stands, key=lambda x: x["number"])

                    booking_form = DashboardBookingForm(
                        initial={
                            "arrival_date": selected_arrival,
                            "departure_date": selected_departure,
                        },
                        available_stands=available_stands,
                    )
            else:
                booking_form = DashboardBookingForm(request.POST, available_stands=Stand.objects.none())

        # STEP 2: Create booking
        elif action == "book":
            selected_arrival_raw = request.POST.get("arrival_date")
            selected_departure_raw = request.POST.get("departure_date")

            temp_form = DashboardBookingForm(request.POST)

            if temp_form.is_valid():
                selected_arrival = temp_form.cleaned_data["arrival_date"]
                selected_departure = temp_form.cleaned_data["departure_date"]

                arrival_dt = datetime.combine(selected_arrival, time(12, 0))
                departure_dt = datetime.combine(selected_departure, time(12, 0))

                overlapping = BookingStand.objects.filter(
                    is_active=True,
                    booking__arrival_datetime__lt=departure_dt,
                    booking__departure_datetime__gt=arrival_dt,
                ).select_related("stand", "booking", "booking__user")

                booked_stand_ids = set()
                booked_stands = []

                for bs in overlapping:
                    if bs.stand_id and bs.stand_id not in booked_stand_ids:
                        booked_stand_ids.add(bs.stand_id)
                        booked_stands.append({
                            "number": bs.stand.number,
                            "name": bs.booking.user.get_full_name().strip() or bs.booking.user.email,
                        })

                available_stands = Stand.objects.exclude(id__in=booked_stand_ids).order_by("number")

                booking_form = DashboardBookingForm(request.POST, available_stands=available_stands)

                if booking_form.is_valid():
                    stand = booking_form.cleaned_data["stand"]

                    if not stand:
                        messages.error(request, "Please select an available stand.")
                    else:
                        overlap = BookingStand.objects.filter(
                            stand=stand,
                            is_active=True,
                            booking__arrival_datetime__lt=departure_dt,
                            booking__departure_datetime__gt=arrival_dt,
                        ).exists()

                        if overlap:
                            messages.error(request, f"Stand {stand.number} is no longer available.")
                        else:
                            booking = Booking.objects.create(
                                user=request.user,
                                arrival_datetime=arrival_dt,
                                departure_datetime=departure_dt,
                                booking_mode="REQUEST",
                                status="PENDING",
                                payment_status="PENDING",
                                attendance_status="PENDING",
                            )

                            BookingStand.objects.create(
                                booking=booking,
                                stand=stand,
                                approval_status="PENDING",
                                is_active=True,
                            )

                            messages.success(request, f"Booking created successfully for Stand {stand.number}.")
                            return redirect("dashboard")
            else:
                booking_form = DashboardBookingForm(request.POST, available_stands=Stand.objects.none())

        else:
            booking_form = DashboardBookingForm()

    else:
        booking_form = DashboardBookingForm()

    context = {
        "today": today,
        "booking_form": booking_form,
        "bookings": user_bookings,
        "available_stands": [stand.number for stand in available_stands],
        "booked_stands": booked_stands,
    }
    return render(request, "dashboard.html", context)

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from stands.models import Stand
from .models import BookingStand


def stand_report_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="stand_report.pdf"'

    p = canvas.Canvas(response, pagesize=A4)

    y = 800

    stands = Stand.objects.all().order_by("number")

    for stand in stands:
        booking = BookingStand.objects.filter(
            stand=stand,
            is_active=True
        ).select_related("booking", "booking__user").first()

        if booking:
            name = booking.booking.user.get_full_name().strip() or booking.booking.user.email
            status = f"BOOKED - {name}"
        else:
            status = "AVAILABLE"

        p.drawString(100, y, f"Stand {stand.number} - {status}")

        y -= 20

        if y < 50:
            p.showPage()
            y = 800

    p.save()
    return response

    
