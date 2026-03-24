from django.contrib import admin
from .models import CustomUser, Profile


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_staff", "is_superuser")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "membership_type", "owned_stand", "savof_code", "membership_expiry_date")
