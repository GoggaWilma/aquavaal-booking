from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Profile, CustomUser
from .resources import ProfileResource


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "is_staff", "is_active")


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    resource_class = ProfileResource

    list_display = (
        "user",
        "surname",
        "call_name",
        "membership_type",
        "owned_stand",
        "savof_code",
    )
