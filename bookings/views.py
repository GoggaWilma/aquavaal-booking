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

    context = {
        'today': today,
        'bookings': todays_bookings,
        'total': todays_bookings.count(),
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
    muted_text = HexColor("#566573")

    # Header
    p.setTitle("Aqua Vaal Stand Layout")
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(title_color)
    p.drawString(30, page_height - 30, "Aqua Vaal Stand Layout")

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

    p.drawString(30, page_height - 48, period_text)

    # Legend
    legend_y = page_height - 72
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(black)
    p.drawString(30, legend_y, "Legend:")

    p.setFillColor(available_color)
    p.rect(75, legend_y - 8, 12, 12, fill=1, stroke=0)
    p.setFillColor(black)
    p.setFont("Helvetica", 10)
    p.drawString(92, legend_y - 6, "Available")

    p.setFillColor(booked_color)
    p.rect(160, legend_y - 8, 12, 12, fill=1, stroke=0)
    p.setFillColor(black)
    p.drawString(177, legend_y - 6, "Booked")

    stands = Stand.objects.all().order_by("number")

    # Grid layout
    cols = 4
    margin_x = 30
    margin_y_top = 100
    margin_y_bottom = 30
    gap_x = 12
    gap_y = 14

    usable_width = page_width - (margin_x * 2)
    box_width = (usable_width - (gap_x * (cols - 1))) / cols
    box_height = 78

    x = margin_x
    y = page_height - margin_y_top
    col = 0

    for stand in stands:
        qs = BookingStand.objects.filter(
            stand=stand,
            is_active=True
        ).select_related("booking", "booking__user")

        if arrival and departure:
            qs = qs.filter(
                booking__arrival_datetime__lt=departure,
                booking__departure_datetime__gt=arrival,
            )
        elif arrival:
            qs = qs.filter(booking__departure_datetime__gt=arrival)
        elif departure:
            qs = qs.filter(booking__arrival_datetime__lt=departure)

        booking_stand = qs.order_by("booking__arrival_datetime").first()

        is_booked = booking_stand is not None
        status_color = booked_color if is_booked else available_color
        status_text = "BOOKED" if is_booked else "AVAILABLE"

        # Outer box
        p.setFillColor(box_bg)
        p.setStrokeColor(border_color)
        p.roundRect(x, y - box_height, box_width, box_height, 8, fill=1, stroke=1)

        # Status banner
        p.setFillColor(status_color)
        p.roundRect(x + 8, y - 22, 68, 16, 4, fill=1, stroke=0)
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 8)
        p.drawString(x + 17, y - 17, status_text)

        # Stand title
        p.setFillColor(title_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(x + 84, y - 17, f"Stand {stand.number}")

        # Details
        p.setFillColor(black)
        p.setFont("Helvetica", 9)

        if is_booked:
            booking = booking_stand.booking
            if booking.user:
                guest_name = booking.user.get_full_name().strip() or booking.user.email
            else:
                guest_name = "Guest assigned"

            guest_line = f"Name: {guest_name}"
            date_line = (
                f"{booking.arrival_datetime.strftime('%d %b')} - "
                f"{booking.departure_datetime.strftime('%d %b')}"
            )
        else:
            guest_line = "Name: -"
            date_line = "Ready to book"

        # Clip long names a bit
        if len(guest_line) > 32:
            guest_line = guest_line[:29] + "..."

        p.drawString(x + 10, y - 40, guest_line)
        p.setFillColor(muted_text)
        p.drawString(x + 10, y - 54, date_line)

        # Next box position
        col += 1
        if col == cols:
            col = 0
            x = margin_x
            y -= (box_height + gap_y)
        else:
            x += (box_width + gap_x)

        # New page
        if y - box_height < margin_y_bottom:
            p.showPage()
            page_width, page_height = landscape(A4)

            # Reset header on new page
            p.setFont("Helvetica-Bold", 20)
            p.setFillColor(title_color)
            p.drawString(30, page_height - 30, "Aqua Vaal Stand Layout")

            p.setFont("Helvetica", 10)
            p.setFillColor(black)
            p.drawString(30, page_height - 48, period_text)

            p.setFont("Helvetica-Bold", 10)
            p.drawString(30, page_height - 72, "Legend:")
            p.setFillColor(available_color)
            p.rect(75, page_height - 80, 12, 12, fill=1, stroke=0)
            p.setFillColor(black)
            p.setFont("Helvetica", 10)
            p.drawString(92, page_height - 78, "Available")
            p.setFillColor(booked_color)
            p.rect(160, page_height - 80, 12, 12, fill=1, stroke=0)
            p.setFillColor(black)
            p.drawString(177, page_height - 78, "Booked")

            x = margin_x
            y = page_height - margin_y_top
            col = 0

    p.save()
    return response
