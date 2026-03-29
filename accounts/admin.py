from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import CustomUser
from .resources import UserResource


@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin):
    resource_class = UserResource
    list_display = ("email", "is_active")
