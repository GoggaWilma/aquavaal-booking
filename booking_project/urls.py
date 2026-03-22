
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("Aquavaal Booking System is Live 🎣")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('bookings.urls')),  # 👈 main app
]
