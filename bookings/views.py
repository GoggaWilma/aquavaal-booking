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
    return render(request, 'dashboard.html')
    
    today = timezone.now().date()

    todays_bookings = Booking.objects.filter(date=today)

    context = {
        'today': today,
        'bookings': todays_bookings,
        'total': todays_bookings.count(),
    }

    return render(request, 'dashboard.html', context)

from datetime import datetime

from django.http import HttpResponse
from django.utils.dateparse import parse_datetime, parse_date
from django.contrib.admin.views.decorators import staff_member_required

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, white, HexColor
from reportlab.pdfgen import canvas

from .models import BookingStand
from stands.models import Stand


def _parse_report_date(value, end_of_day=False):
    if not value:
        return None

    dt = parse_datetime(value)
    if dt:
        return dt

    d = parse_date(value)
    if d:
        if end_of_day:
            return datetime.combine(d, datetime.max.time().replace(microsecond=0))
        return datetime.combine(d, datetime.min.time())

    return None


@staff_member_required
def stand_report_pdf(request):
    arrival = _parse_report_date(request.GET.get("arrival"))
    departure = _parse_report_date(request.GET.get("departure"), end_of_day=True)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="stand_report.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Colors
    title_color = HexColor("#1F4E79")
    booked_color = HexColor("#C0392B")
    available_color = HexColor("#2E8B57")
    light_gray = HexColor("#F4F6F7")
    border_color = HexColor("#D5D8DC")

    # Header
    p.setTitle("Aqua Vaal Stand Report")
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(title_color)
    p.drawString(40, height - 40, "Aqua Vaal Stand Availability Report")

    p.setFont("Helvetica", 10)
    p.setFillColor(black)

    if arrival and departure:
        p.drawString(
            40,
            height - 60,
            f"Period: {arrival.strftime('%Y-%m-%d %H:%M')} to {departure.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        p.drawString(
            40,
            height - 60,
            "Period: All active bookings considered"
        )

    # Legend
    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, height - 85, "Legend:")
    p.setFillColor(available_color)
    p.rect(90, height - 92, 12, 12, fill=1, stroke=0)
    p.setFillColor(black)
    p.drawString(108, height - 90, "Available")

    p.setFillColor(booked_color)
    p.rect(175, height - 92, 12, 12, fill=1, stroke=0)
    p.setFillColor(black)
    p.drawString(193, height - 90, "Booked")

    # Layout settings
    stands = Stand.objects.all().order_by("number")
    cols = 3
    box_width = 165
    box_height = 60
    gap_x = 12
    gap_y = 14
    start_x = 40
    start_y = height - 130

    x = start_x
    y = start_y
    col_index = 0

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

        booking_stand = qs.first()

        is_booked = booking_stand is not None
        box_color = booked_color if is_booked else available_color
        status_text = "BOOKED" if is_booked else "AVAILABLE"

        # Box background
        p.setFillColor(light_gray)
        p.setStrokeColor(border_color)
        p.roundRect(x, y - box_height, box_width, box_height, 8, fill=1, stroke=1)

        # Status pill
        p.setFillColor(box_color)
        p.roundRect(x + 8, y - 22, 58, 16, 6, fill=1, stroke=0)

        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 8)
        p.drawString(x + 16, y - 17, status_text)

        # Stand title
        p.setFillColor(title_color)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(x + 78, y - 18, f"Stand {stand.number}")

        # Occupant / details
        p.setFillColor(black)
        p.setFont("Helvetica", 9)

        if is_booked:
            booking = booking_stand.booking
            guest_name = ""
            if booking.user:
                guest_name = booking.user.get_full_name().strip() or booking.user.email

            line_1 = f"Guest: {guest_name}" if guest_name else "Guest: Assigned"
            line_2 = f"Stay: {booking.arrival_datetime.strftime('%d %b')} - {booking.departure_datetime.strftime('%d %b')}"
        else:
            line_1 = "Guest: -"
            line_2 = "Ready to book"

        p.drawString(x + 10, y - 38, line_1[:32])
        p.drawString(x + 10, y - 50, line_2[:32])

        # Move to next cell
        col_index += 1
        if col_index == cols:
            col_index = 0
            x = start_x
            y -= (box_height + gap_y)
        else:
            x += (box_width + gap_x)

        # New page if needed
        if y < 80:
            p.showPage()
            x = start_x
            y = height - 50
            col_index = 0

    p.save()
    return response

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import BookingStand
from stands.models import Stand


@staff_member_required
def stand_report_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="stand_report.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    y = 800

    stands = Stand.objects.all().order_by("number")

    for stand in stands:
        booked = BookingStand.objects.filter(
            stand=stand,
            is_active=True
        ).exists()

        status = "BOOKED" if booked else "AVAILABLE"
        p.drawString(100, y, f"Stand {stand.number} - {status}")

        y -= 20
        if y < 50:
            p.showPage()
            y = 800

    p.save()
    return response
