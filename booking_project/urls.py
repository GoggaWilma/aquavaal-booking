from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home(request):
    return HttpResponse("Aquavaal Booking System is Live 🎣")

urlpatterns = [
    path('', home),   # 👈 THIS LINE FIXES YOUR ISSUE
    path('admin/', admin.site.urls),
]
