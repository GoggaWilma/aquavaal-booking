from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

from stands.models import Stand
from .models import Booking, BookingStand
from .forms import DashboardBookingForm

@login_required
def dashboard(request):
    today = timezone.now().date()
    user_bookings = Booking.objects.filter(user=request.user).order_by("-created_at")[:10]

    available_stands = Stand.objects.none()
    selected_stand_id = None

    stand_sections = [
        ("Eskom", [1, 2]),
        ("Owners A", [3]),
        ("Boat Club", [4, 5, 6, 7]),
        ("Owners B", [8, 9, 10, 11, 12, 13, 14]),
        ("Public", [15, 16, 17, 18, 19, 20, 21]),
        ("Owners C", [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]),
    ]

    booked_stands = []
    available_stand_numbers = []

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "check":
            temp_form = DashboardBookingForm(request.POST)

            if temp_form.is_valid():
                arrival_date = temp_form.cleaned_data["arrival_date"]
                departure_date = temp_form.cleaned_data["departure_date"]

                arrival_dt = datetime.combine(arrival_date, time(12, 0))
                departure_dt = datetime.combine(departure_date, time(12, 0))

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
                                "id": bs.stand.id,
                                "number": bs.stand.number,
                                "name": bs.booking.user.get_full_name().strip() or bs.booking.user.email,
                            })

                    available_stands = Stand.objects.exclude(id__in=booked_stand_ids).order_by("number")
                    available_stand_numbers = list(available_stands.values_list("number", flat=True))
                    booked_stands = sorted(booked_stands, key=lambda x: x["number"])

                    booking_form = DashboardBookingForm(
                        initial={
                            "arrival_date": arrival_date,
                            "departure_date": departure_date,
                        },
                        available_stands=available_stands,
                    )
            else:
                booking_form = DashboardBookingForm(request.POST, available_stands=Stand.objects.none())

        elif action == "book":
            temp_form = DashboardBookingForm(request.POST)

            arrival_date_raw = request.POST.get("arrival_date")
            departure_date_raw = request.POST.get("departure_date")
            selected_stand_id = request.POST.get("stand")

            if temp_form.is_valid():
                arrival_date = temp_form.cleaned_data["arrival_date"]
                departure_date = temp_form.cleaned_data["departure_date"]

                arrival_dt = datetime.combine(arrival_date, time(12, 0))
                departure_dt = datetime.combine(departure_date, time(12, 0))

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
                            "id": bs.stand.id,
                            "number": bs.stand.number,
                            "name": bs.booking.user.get_full_name().strip() or bs.booking.user.email,
                        })

                available_stands = Stand.objects.exclude(id__in=booked_stand_ids).order_by("number")
                available_stand_numbers = list(available_stands.values_list("number", flat=True))
                booked_stands = sorted(booked_stands, key=lambda x: x["number"])

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
        "booked_stands": booked_stands,
        "available_stand_numbers": available_stand_numbers,
        "selected_stand_id": int(selected_stand_id) if selected_stand_id else None,
        "stand_sections": stand_sections,
    }

    return render(request, "dashboard.html", context)

def stand_report_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="stand_layout_report.pdf"'

    p = canvas.Canvas(response, pagesize=landscape(A4))
    page_width, page_height = landscape(A4)

    # Colors
    title_color = HexColor("#1F4E79")
    booked_color = HexColor("#C0392B")
    available_color = HexColor("#2E8B57")
    border_color = HexColor("#D5D8DC")
    box_bg = HexColor("#F8F9F9")
    section_color = HexColor("#154360")
    muted_text = HexColor("#566573")

    # Stand group layout
    stand_sections = [
        ("Eskom", [1, 2]),
        ("Owners A", [3]),
        ("Boat Club", [4, 5, 6, 7]),
        ("Owners B", [8, 9, 10, 11, 12, 13, 14]),
        ("Public", [15, 16, 17, 18, 19, 20, 21]),
        ("Owners C", [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]),
    ]

    stands = Stand.objects.all().order_by("number")
    stand_lookup = {stand.number: stand for stand in stands}

    booking_stands = BookingStand.objects.filter(
        is_active=True
    ).select_related("booking", "booking__user", "stand")

    stand_booking_map = {}
    for bs in booking_stands:
        if bs.stand_id and bs.stand_id not in stand_booking_map:
            stand_booking_map[bs.stand_id] = bs

    def draw_header():
        p.setTitle("Aqua Vaal Stand Layout")
        p.setFont("Helvetica-Bold", 20)
        p.setFillColor(title_color)
        p.drawString(25, page_height - 28, "Aqua Vaal Stand Layout")

        p.setFont("Helvetica", 10)
        p.setFillColor(black)
        p.drawString(25, page_height - 45, "Live grouped stand layout")

        p.setFont("Helvetica-Bold", 10)
        p.drawString(25, page_height - 65, "Legend:")

        p.setFillColor(available_color)
        p.rect(72, page_height - 72, 12, 12, fill=1, stroke=0)
        p.setFillColor(black)
        p.setFont("Helvetica", 10)
        p.drawString(90, page_height - 70, "Available")

        p.setFillColor(booked_color)
        p.rect(160, page_height - 72, 12, 12, fill=1, stroke=0)
        p.setFillColor(black)
        p.drawString(178, page_height - 70, "Booked")

        p.setFont("Helvetica-Oblique", 9)
        p.setFillColor(muted_text)
        p.drawString(250, page_height - 70, "Left to right: Stand 1 to Stand 40 along the river")

    def draw_stand_box(x, y, width, height, stand_number):
        stand = stand_lookup.get(stand_number)
        booking_stand = stand_booking_map.get(stand.id) if stand else None

        is_booked = booking_stand is not None
        status_color = booked_color if is_booked else available_color
        status_text = "BOOKED" if is_booked else "AVAILABLE"

        p.setFillColor(box_bg)
        p.setStrokeColor(border_color)
        p.roundRect(x, y - height, width, height, 6, fill=1, stroke=1)

        p.setFillColor(status_color)
        p.roundRect(x + 6, y - 20, 56, 14, 4, fill=1, stroke=0)

        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 7)
        p.drawString(x + 12, y - 15, status_text)

        p.setFillColor(title_color)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(x + 68, y - 15, f"Stand {stand_number}")

        p.setFillColor(black)
        p.setFont("Helvetica", 7)

        if is_booked:
            booking = booking_stand.booking
            guest_name = booking.user.get_full_name().strip() or booking.user.email or "-"

            if len(guest_name) > 20:
                guest_name = guest_name[:17] + "..."

            date_text = (
                f"{booking.arrival_datetime.strftime('%d %b')} - "
                f"{booking.departure_datetime.strftime('%d %b')}"
            )
        else:
            guest_name = "-"
            date_text = "Ready to book"

        p.drawString(x + 8, y - 34, guest_name)
        p.setFillColor(muted_text)
        p.drawString(x + 8, y - 46, date_text)

    draw_header()

    left_margin = 25
    right_margin = 25
    top_y = page_height - 95
    bottom_margin = 25
    section_gap = 16
    row_gap = 8

    box_height = 52
    usable_width = page_width - left_margin - right_margin
    max_cols = 7
    box_gap = 6
    box_width = (usable_width - (box_gap * (max_cols - 1))) / max_cols

    current_y = top_y

    for section_name, stand_numbers in stand_sections:
        needed_height = 20 + box_height + section_gap

        if current_y - needed_height < bottom_margin:
            p.showPage()
            draw_header()
            current_y = top_y

        p.setFillColor(section_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(left_margin, current_y, section_name)

        current_y -= 10

        x = left_margin
        col = 0
        row_top_y = current_y - 6

        for index, stand_number in enumerate(stand_numbers):
            draw_stand_box(x, row_top_y, box_width, box_height, stand_number)

            col += 1
            if col == max_cols and index != len(stand_numbers) - 1:
                col = 0
                x = left_margin
                row_top_y -= (box_height + row_gap)

                if row_top_y - box_height < bottom_margin:
                    p.showPage()
                    draw_header()
                    current_y = top_y
                    p.setFillColor(section_color)
                    p.setFont("Helvetica-Bold", 12)
                    p.drawString(left_margin, current_y, f"{section_name} (continued)")
                    current_y -= 10
                    row_top_y = current_y - 6
            else:
                x += (box_width + box_gap)

        rows_used = ((len(stand_numbers) - 1) // max_cols) + 1
        current_y = current_y - (rows_used * (box_height + row_gap)) - section_gap

    p.save()
    return response
