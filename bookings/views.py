from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to Aqua Vaal Hengelklub 🎣")

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from .models import Booking, BookingStand
from .forms import BookingForm

from django.utils import timezone
from django.db.models import Sum, Count
from django.shortcuts import render


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
