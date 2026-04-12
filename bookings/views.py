from django.utils import timezone
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

from datetime import datetime, time, timedelta

from stands.models import Stand
from .models import Booking, BookingStand
from .forms import DashboardBookingForm

from django.core.mail import send_mail
from django.conf import settings

@login_required
def dashboard(request):
    selected_stand_id = request.GET.get("stand_id")
    selected_stand_number = None

    if selected_stand_id:
        try:
            selected_stand_number = Stand.objects.get(id=selected_stand_id).number
        except Stand.DoesNotExist:
            selected_stand_id = None
            selected_stand_number = None

    today = timezone.now().date()
    user_bookings = Booking.objects.filter(user=request.user).order_by("-created_at")[:10]

    stand_sections = [
        ("Eskom Members", [1, 2]),
        ("Owner 3", [3]),
        ("Boat Club Members", [4, 5, 6]),
        ("Owners 7 to 14", [7, 8, 9, 10, 11, 12, 13, 14]),
        ("Public", [15, 16, 17, 18, 19, 20, 21]),
        ("Owners 22 to 40", [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]),
    ]

    available_stands = Stand.objects.none()
    available_stand_numbers = []

    pending_stands = []
    booked_stands = []
    unavailable_stands = []

    pending_stand_ids = set()
    booked_stand_ids = set()
    unavailable_stand_ids = set()

    arrival_date = request.GET.get("arrival_date")
    departure_date = request.GET.get("departure_date")

    booking_form = DashboardBookingForm()

    if arrival_date and departure_date:
        booking_form = DashboardBookingForm(request.GET)

        if booking_form.is_valid():
            arrival_date = booking_form.cleaned_data["arrival_date"]
            departure_date = booking_form.cleaned_data["departure_date"]

            arrival_dt = timezone.make_aware(datetime.combine(arrival_date, time(12, 0)))
            departure_dt = timezone.make_aware(datetime.combine(departure_date, time(12, 0)))

            if departure_dt <= arrival_dt:
                messages.error(request, "Departure date must be after arrival date.")
            else:
                overlapping = BookingStand.objects.filter(
                    is_active=True,
                    booking__arrival_datetime__lt=departure_dt,
                    booking__departure_datetime__gt=arrival_dt,
                ).select_related("stand", "booking", "booking__user")

                for bs in overlapping:
                    if not bs.stand_id:
                        continue

                    if bs.approval_status == "UNAVAILABLE":
                        if bs.stand_id not in unavailable_stand_ids:
                            unavailable_stand_ids.add(bs.stand_id)
                            unavailable_stands.append({
                                "id": bs.id,
                                "number": bs.stand.number,
                                "reason": bs.unavailable_reason or "Unavailable",
                            })

                    elif bs.approval_status in ["APPROVED", "READY_FOR_GATE"]:
                        booked_stand_ids.add(bs.stand_id)

                        existing = next((s for s in booked_stands if s["number"] == bs.stand.number), None)

                        entry = {
                            "name": bs.booking.display_name(),
                            "arrival": bs.booking.arrival_datetime.strftime("%d %b %Y"),
                            "departure": bs.booking.departure_datetime.strftime("%d %b %Y"),
                        }

                        if existing:
                            existing["bookings"].append(entry)
                        else:
                            booked_stands.append({
                                "id": bs.id,
                                "number": bs.stand.number,
                                "bookings": [entry],
                                "name": entry["name"],
                                "arrival": entry["arrival"],
                                "departure": entry["departure"],
                            })


                    elif bs.approval_status == "PENDING":
                        pending_stand_ids.add(bs.stand_id)

                        existing = next((s for s in pending_stands if s["number"] == bs.stand.number), None)

                        entry = {
                            "name": bs.booking.display_name(),
                            "arrival": bs.booking.arrival_datetime.strftime("%d %b %Y"),
                            "departure": bs.booking.departure_datetime.strftime("%d %b %Y"),
                        }

                        if existing:
                            existing["bookings"].append(entry)
                        else:
                            pending_stands.append({
                                "id": bs.id,
                                "number": bs.stand.number,
                                "bookings": [entry],
                                "name": entry["name"],
                                "arrival": entry["arrival"],
                                "departure": entry["departure"],
                            })

                blocked_ids = booked_stand_ids | unavailable_stand_ids | pending_stand_ids

                available_stands = Stand.objects.exclude(id__in=blocked_ids).order_by("number")
                available_stand_numbers = list(
                    available_stands.values_list("number", flat=True)
                )

                booked_stands = sorted(booked_stands, key=lambda x: x["number"])
                pending_stands = sorted(pending_stands, key=lambda x: x["number"])
                unavailable_stands = sorted(unavailable_stands, key=lambda x: x["number"])

                booking_form = DashboardBookingForm(
                    initial={
                        "arrival_date": arrival_date,
                        "departure_date": departure_date,
                        "stand": selected_stand_id,
                    },
                    available_stands=available_stands,
                )

    if request.method == "POST":
        selected_stand_id = request.POST.get("stand")
        selected_stand_number = None

        if selected_stand_id:
            try:
                selected_stand_number = Stand.objects.get(id=selected_stand_id).number
            except Stand.DoesNotExist:
                selected_stand_id = None
                selected_stand_number = None

        arrival_raw = request.POST.get("arrival_date")
        departure_raw = request.POST.get("departure_date")

        temp_form = DashboardBookingForm(
            {
                "arrival_date": arrival_raw,
                "departure_date": departure_raw,
                "stand": selected_stand_id,
            },
            available_stands=available_stands if available_stands.exists() else Stand.objects.all(),
        )

        if temp_form.is_valid():
            arrival_date = temp_form.cleaned_data["arrival_date"]
            departure_date = temp_form.cleaned_data["departure_date"]
            stand = temp_form.cleaned_data["stand"]

            arrival_dt = timezone.make_aware(datetime.combine(arrival_date, time(12, 0)))
            departure_dt = timezone.make_aware(datetime.combine(departure_date, time(12, 0)))

            overlap = BookingStand.objects.filter(
                stand=stand,
                is_active=True,
                booking__arrival_datetime__lt=departure_dt,
                booking__departure_datetime__gt=arrival_dt,
                approval_status__in=["PENDING", "APPROVED", "READY_FOR_GATE", "UNAVAILABLE"],
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

                try:
                    send_mail(
                        subject=f"🎣 New Booking - Stand {stand.number}",
                        message=f"""
                New booking created:

                Name: {booking.display_name()}
                Stand: {stand.number}
                Arrival: {booking.arrival_datetime.strftime('%d %b %Y %H:%M')}
                Departure: {booking.departure_datetime.strftime('%d %b %Y %H:%M')}
                Status: {booking.status}
                """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=["ivor.engelbrecht@gmail.com"],
                    fail_silently=False,
                    )
                except Exception as e:
                    print("Email failed:", e)

                messages.success(request, f"Booking created successfully for Stand {stand.number}.")
                return redirect("dashboard")
        else:
            messages.error(request, "Please select dates and an available stand.")

    context = {
        "today": today,
        "booking_form": booking_form,
        "bookings": user_bookings,
        "available_stand_numbers": available_stand_numbers,
        "pending_stands": pending_stands,
        "booked_stands": booked_stands,
        "unavailable_stands": unavailable_stands,
        "pending_stand_numbers": [s["number"] for s in pending_stands],
        "booked_stand_numbers": [s["number"] for s in booked_stands],
        "unavailable_stand_numbers": [s["number"] for s in unavailable_stands],
        "selected_stand_id": int(selected_stand_id) if selected_stand_id else None,
        "selected_stand_number": selected_stand_number,
        "stand_sections": stand_sections,
        "arrival_date": request.GET.get("arrival_date", ""),
        "departure_date": request.GET.get("departure_date", ""),
    }

    return render(request, "dashboard.html", context)

@login_required
def booking_stand_action(request):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect("dashboard")

    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect("dashboard")

    booking_stand_id = request.POST.get("booking_stand_id")
    action = request.POST.get("action")

    if not booking_stand_id or not action:
        messages.error(request, "Missing booking stand action details.")
        return redirect("dashboard")

    try:
        booking_stand = BookingStand.objects.select_related("booking", "stand").get(id=booking_stand_id)
    except BookingStand.DoesNotExist:
        messages.error(request, "Booking stand not found.")
        return redirect("dashboard")

    if action == "approve":
        booking_stand.approval_status = "APPROVED"
        booking_stand.booking.status = "APPROVED"
        booking_stand.booking.save(update_fields=["status"])
        booking_stand.save(update_fields=["approval_status"])

        # Email to Ivor
        try:
            send_mail(
                subject=f"✅ Booking Approved - Stand {booking_stand.stand.number}",
                message=f"""
    Booking approved:

    Name: {booking_stand.booking.display_name()}
    Stand: {booking_stand.stand.number}
    Arrival: {booking_stand.booking.arrival_datetime.strftime('%d %b %Y %H:%M')}
    Departure: {booking_stand.booking.departure_datetime.strftime('%d %b %Y %H:%M')}
    Status: {booking_stand.booking.status}
    """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["ivor.engelbrecht@gmail.com"],
                fail_silently=False,
            )
        except Exception as e:
            print("Approve email failed:", e)

        # Email to user
        if booking_stand.booking.user and booking_stand.booking.user.email:
            try:
                send_mail(
                    subject=f"Your booking was approved - Stand {booking_stand.stand.number}",
                    message=f"""
    Good news, your booking has been approved.
 
    Stand: {booking_stand.stand.number}
    Arrival: {booking_stand.booking.arrival_datetime.strftime('%d %b %Y %H:%M')}
    Departure: {booking_stand.booking.departure_datetime.strftime('%d %b %Y %H:%M')}
    Status: {booking_stand.booking.status}

    Thank you.
    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[booking_stand.booking.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print("User approve email failed:", e)

        messages.success(request, f"Stand {booking_stand.stand.number} approved.")


    elif action == "reject":
        booking_stand.approval_status = "REJECTED"
        booking_stand.booking.status = "REJECTED"
        booking_stand.booking.save(update_fields=["status"])
        booking_stand.save(update_fields=["approval_status"])

        # Email to Ivor
        try:
            send_mail(
                subject=f"❌ Booking Rejected - Stand {booking_stand.stand.number}",
                message=f"""
    Booking rejected:

    Name: {booking_stand.booking.display_name()}
    Stand: {booking_stand.stand.number}
    Arrival: {booking_stand.booking.arrival_datetime.strftime('%d %b %Y %H:%M')}
    Departure: {booking_stand.booking.departure_datetime.strftime('%d %b %Y %H:%M')}
    Status: {booking_stand.booking.status}
    """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["ivor.engelbrecht@gmail.com"],
                fail_silently=False,
            )
        except Exception as e:
            print("Reject email failed:", e)

        # Email to user
        if booking_stand.booking.user and booking_stand.booking.user.email:
            try:
                send_mail(
                    subject=f"Your booking was rejected - Stand {booking_stand.stand.number}",
                    message=f"""
    Your booking was unfortunately rejected.

    Stand: {booking_stand.stand.number}
    Arrival: {booking_stand.booking.arrival_datetime.strftime('%d %b %Y %H:%M')}
    Departure: {booking_stand.booking.departure_datetime.strftime('%d %b %Y %H:%M')}
    Status: {booking_stand.booking.status}

    Please contact Ivor if you need assistance.
    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[booking_stand.booking.user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print("User reject email failed:", e)

        messages.success(request, f"Stand {booking_stand.stand.number} rejected.")


    else:
        messages.error(request, "Unknown action.")

    return redirect("dashboard")


def stand_report_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    
    if request.GET.get("download") == "1":
        response["Content-Disposition"] = 'attachment; filename="stand_layout_report.pdf"'
    
    else:
        response["Content-Disposition"] = 'inline; filename="stand_layout_report.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    page_width, page_height = A4

    title_color = HexColor("#1F4E79")

    available_color = HexColor("#2ECC71")
    pending_color = HexColor("#F4D03F")
    booked_color = HexColor("#3498DB")
    unavailable_color = HexColor("#E74C3C")

    border_color = HexColor("#D5D8DC")
    box_bg = HexColor("#F8F9F9")
    section_color = HexColor("#154360")
    muted_text = HexColor("#566573")

    stand_sections = [
        ("Eskom Members", [1, 2]),
        ("Owner 3", [3]),
        ("Boat Club Members", [4, 5, 6]),
        ("Owners 7 to 14", [7, 8, 9, 10, 11, 12, 13, 14]),
        ("Public", [15, 16, 17, 18, 19, 20, 21]),
        ("Owners 22 to 40", [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]),
    ]

    stands = Stand.objects.all().order_by("number")
    stand_lookup = {stand.number: stand for stand in stands}

    yesterday = timezone.localdate() - timedelta(days=1)

    booking_stands = BookingStand.objects.filter(
        is_active=True,
        booking__departure_datetime__date__gte=yesterday,
    ).select_related("booking", "booking__user", "stand").order_by(
        "booking__arrival_datetime"
    )

    stand_booking_map = {}
    for bs in booking_stands:
        if bs.stand_id:
            stand_booking_map.setdefault(bs.stand_id, []).append(bs)

    def draw_header():
        p.setTitle("Aqua Vaal Stand Layout")
        p.setFont("Helvetica-Bold", 18)
        p.setFillColor(title_color)
        p.drawString(25, page_height - 28, "Aqua Vaal Stand Layout")

        p.setFont("Helvetica", 10)
        p.setFillColor(black)
        p.drawString(25, page_height - 45, "Current and upcoming stand bookings")

        p.setFont("Helvetica-Bold", 10)
        p.drawString(25, page_height - 65, "Legend:")

        p.setFillColor(available_color)
        p.rect(80, page_height - 72, 10, 10, fill=1, stroke=0)
        p.setFillColor(black)
        p.drawString(95, page_height - 70, "Available")

        p.setFillColor(pending_color)
        p.rect(160, page_height - 72, 10, 10, fill=1, stroke=0)
        p.setFillColor(black)
        p.drawString(175, page_height - 70, "Pending")

        p.setFillColor(booked_color)
        p.rect(230, page_height - 72, 10, 10, fill=1, stroke=0)
        p.setFillColor(black)
        p.drawString(245, page_height - 70, "Booked")

        p.setFillColor(unavailable_color)
        p.rect(300, page_height - 72, 10, 10, fill=1, stroke=0)
        p.setFillColor(black)
        p.drawString(315, page_height - 70, "Unavailable")

    def draw_stand_box(x, y, width, height, stand_number):
        stand = stand_lookup.get(stand_number)
        booking_list = stand_booking_map.get(stand.id, []) if stand else []

        pending_items = [bs for bs in booking_list if bs.approval_status == "PENDING"]
        unavailable_items = [bs for bs in booking_list if bs.approval_status == "UNAVAILABLE"]
        booked_items = [bs for bs in booking_list if bs.approval_status in ["APPROVED", "READY_FOR_GATE"]]

        if unavailable_items:
            status_color = unavailable_color
            status_text = "UNAVAILABLE"
        elif booked_items:
            status_color = booked_color
            status_text = "BOOKED"
        elif pending_items:
            status_color = pending_color
            status_text = "PENDING"
        else:
            status_color = available_color
            status_text = "AVAILABLE"

        p.setFillColor(box_bg)
        p.setStrokeColor(border_color)
        p.roundRect(x, y - height, width, height, 6, fill=1, stroke=1)

        p.setFillColor(status_color)
        p.roundRect(x + 6, y - 20, 68, 14, 4, fill=1, stroke=0)

        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 7)
        p.drawString(x + 12, y - 15, status_text)

        p.setFillColor(title_color)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(x + 80, y - 15, f"Stand {stand_number}")

        if unavailable_items:
            y_offset = 34
            for booking_stand in unavailable_items[:2]:
                reason = booking_stand.unavailable_reason or "No reason given"
                p.setFillColor(black)
                p.setFont("Helvetica", 6)
                p.drawString(x + 6, y - y_offset, reason[:28])
                y_offset += 10

        elif booked_items:
            y_offset = 34
            for booking_stand in booked_items[:3]:
                booking = booking_stand.booking
                guest_name = booking.display_name()

                date_text = (
                    f"{booking.arrival_datetime.strftime('%d %b')} - "
                    f"{booking.departure_datetime.strftime('%d %b')}"
                )

                p.setFillColor(black)
                p.setFont("Helvetica", 6)
                p.drawString(x + 6, y - y_offset, guest_name[:28])

                p.setFillColor(muted_text)
                p.drawString(x + 6, y - (y_offset + 8), date_text)

                y_offset += 14

        elif pending_items:
            y_offset = 34
            for booking_stand in pending_items[:2]:
                booking = booking_stand.booking
                guest_name = booking.display_name()

                date_text = (
                    f"{booking.arrival_datetime.strftime('%d %b')} - "
                    f"{booking.departure_datetime.strftime('%d %b')}"
                )

                p.setFillColor(black)
                p.setFont("Helvetica", 6)
                p.drawString(x + 6, y - y_offset, guest_name[:28])

                p.setFillColor(muted_text)
                p.drawString(x + 6, y - (y_offset + 8), date_text)

                y_offset += 14

    draw_header()

    left_margin = 25
    right_margin = 25
    top_y = page_height - 120
    bottom_margin = 25
    section_gap = 16
    row_gap = 8

    box_height = 80
    usable_width = page_width - left_margin - right_margin
    max_cols = 4
    box_gap = 8
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

    p.showPage()
    p.save()
    return response
