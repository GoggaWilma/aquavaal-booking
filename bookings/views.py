from accounts.models import Profile
import time
start = time.time()

from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to Aqua Vaal Hengelklub 🎣")

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from .models import Booking, BookingStand

from django.utils import timezone
from django.db.models import Sum, Count
from django.shortcuts import render

from .forms import BookingForm

def some_view(request):
    form = BookingForm()
    return render(request, "some_template.html", {"form": form})

@login_required
def member_dashboard(request):
    bookings = Booking.objects.filter(user=request.user)

    return render(request, "bookings/member_dashboard.html", {
        "bookings": bookings
    })


@login_required
def proceed_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.status == "PARTIAL":
        booking.proceed_with_approved_stands()

    return redirect("member_dashboard")


@staff_member_required
def capture_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.attendance_status != "FINAL":
        booking.payment_status = "PAID"
        booking.attendance_status = "FINAL"
        booking.save()

    return redirect("admin:index")


@login_required
def create_booking(request):

    if request.method == "POST":
        form = BookingForm(request.POST)

        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()

            return redirect("member_dashboard")

    else:
        form = BookingForm()

    return render(request, "bookings/create_booking.html", {
        "form": form
    })

def reports_dashboard(request):
    today = timezone.now().date()

    # Today's bookings
    todays_bookings = Booking.objects.filter(date=today)

    total_bookings = todays_bookings.count()

    total_revenue = todays_bookings.aggregate(
        total=Sum('approved_amount')
    )['total'] or 0

    # Outstanding payments
    outstanding = Booking.objects.filter(
        approved_amount__isnull=True
    ).count()

    context = {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'outstanding': outstanding,
        'today': today,
    }

    return render(request, 'reports/dashboard.html', context)

from django.shortcuts import render
from django.utils import timezone
from .models import Booking

def dashboard(request):
    today = timezone.now().date()
    todays_bookings = Booking.objects.filter(arrival_datetime__date=today)

    profiles = Profile.objects.select_related("user").order_by("-id")[:10]

    context = {
        'today': today,
        'bookings': todays_bookings,
        'total': todays_bookings.count(),
        'profiles': profiles,
    }

    return render(request, 'dashboard.html', context)

    from datetime import datetime, time

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.dateparse import parse_date, parse_datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

from .models import BookingStand
from stands.models import Stand


def _parse_report_datetime(value, is_end=False):
    if not value:
        return None

    dt = parse_datetime(value)
    if dt:
        return dt

    d = parse_date(value)
    if d:
        return datetime.combine(d, time.max if is_end else time.min)

    return None


@staff_member_required
def stand_report_pdf(request):
    arrival = _parse_report_datetime(request.GET.get("arrival"))
    departure = _parse_report_datetime(request.GET.get("departure"), is_end=True)

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

    # Real layout sections
    layout_sections = [
        ("Eskom", [1, 2]),
        ("Owners A", [3]),
        ("Boat Club", [4, 5, 6, 7]),
        ("Owners B", [8, 9, 10, 11, 12, 13, 14]),
        ("Public", [15, 16, 17, 18, 19, 20, 21]),
        ("Owners C", [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]),
    ]

    # Load stands once
    stands = Stand.objects.all().order_by("number")
    stand_lookup = {stand.number: stand for stand in stands}

    # Load bookings once
    booking_stands = BookingStand.objects.filter(
        is_active=True
    ).select_related("booking", "booking__user", "stand")

    if arrival and departure:
        booking_stands = booking_stands.filter(
            booking__arrival_datetime__lt=departure,
            booking__departure_datetime__gt=arrival,
        )
    elif arrival:
        booking_stands = booking_stands.filter(
            booking__departure_datetime__gt=arrival
        )
    elif departure:
        booking_stands = booking_stands.filter(
            booking__arrival_datetime__lt=departure
        )

    # Map stand_id -> bookingstand
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

        if arrival and departure:
            period_text = (
                f"Period: {arrival.strftime('%d %b %Y %H:%M')} "
                f"to {departure.strftime('%d %b %Y %H:%M')}"
            )
        elif arrival:
            period_text = f"From: {arrival.strftime('%d %b %Y %H:%M')}"
        elif departure:
            period_text = f"Until: {departure.strftime('%d %b %Y %H:%M')}"
        else:
            period_text = "Period: All active bookings"

        p.drawString(25, page_height - 45, period_text)

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
        p.drawString(260, page_height - 70, "Left to right: Stand 1 to Stand 40 along the river")

    def draw_stand_box(x, y, width, height, stand_number):
        stand = stand_lookup.get(stand_number)

        if stand:
            booking_stand = stand_booking_map.get(stand.id)
        else:
            booking_stand = None

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
            guest_name = "-"
            if booking.user:
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

    # Layout measurements
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

    for section_name, stand_numbers in layout_sections:
        needed_height = 20 + box_height + section_gap

        if current_y - needed_height < bottom_margin:
            p.showPage()
            draw_header()
            current_y = top_y

        # Section title
        p.setFillColor(section_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(left_margin, current_y, section_name)

        current_y -= 10

        # Draw row(s) for this section
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

        # Move current_y below the section
        rows_used = ((len(stand_numbers) - 1) // max_cols) + 1
        current_y = current_y - (rows_used * (box_height + row_gap)) - section_gap

    p.save()
    return response    

          
    print("PDF generated in:", time.time() - start)
