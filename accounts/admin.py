from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    fk_name = "user"

    fields = (
        "membership_type",
        "owned_stand",
        "surname",
        "first_name",
        "call_name",
        "initials",
        "ID_number",
        "date_of_birth",
        "savof_code",
        "gender",
        "membership_expiry_date",
        "cell_number",
        "house_number",
        "street_name",
        "suburb",
        "city",
        "province",
        "postal_code",
    )


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    inlines = [ProfileInline]

    list_display = ("email", "is_active", "is_staff", "is_superuser")
    search_fields = ("email",)
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "membership_type",
        "owned_stand",
        "membership_expiry_date",
    )
    search_fields = (
        "user__email",
        "surname",
        "first_name",
        "cell_number",
    )
    list_filter = ("membership_type", "gender")
