from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# -------------------------
# CUSTOM USER MANAGER
# -------------------------

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


# -------------------------
# CUSTOM USER
# -------------------------

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        profile = getattr(self, "profile", None)

        if profile:
            call_name = (profile.call_name or "").strip()
            surname = (profile.surname or "").strip()
            full_name = f"{call_name} {surname}".strip()

            if full_name:
                return full_name

            first_name = (profile.first_name or "").strip()
            fallback_name = f"{first_name} {surname}".strip()
            if fallback_name:
                return fallback_name

        full_name = self.get_full_name().strip()
        if full_name:
            return full_name

        return self.email


# -------------------------
# PROFILE MODEL
# -------------------------

class Profile(models.Model):

    MEMBERSHIP_TYPE_CHOICES = [
        ("MEMBER", "Member"),
        ("SOCIAL MEMBER", "Social Member"),
        ("GUEST", "Guest"),
        ("UNPAID", "Unpaid Member"), 
        ("EXPIRED", "Expired Member"),
        ("ESKOM MEMBER", "Eskom Member"),
        ("UNPAID ESKOM", "Unpaid Eskom Member"),
        ("BOAT CLUB MEMBER", "Boat Club Member"),
    ]

    GENDER_CHOICES = [
        ("O", "O Men Masters (50+)"),
        ("M", "M Men Senior (19-49)"),
        ("B", "B Boys Junior (<19)"),
        ("T", "T Ladies Masters (50+)"),
        ("L", "L Ladies Senior (19-49)"),
        ("G", "G Girls Junior (<19)"),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_TYPE_CHOICES,
        default="GUEST"
    )

    owned_stand = models.ForeignKey(
        "stands.Stand",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Stand owned by this member (if applicable)"
    )

    surname = models.CharField(max_length=100, null=True, blank=True) 
    first_name = models.CharField(max_length=100, null=True, blank=True)
    call_name = models.CharField(max_length=100, null=True, blank=True)
    initials = models.CharField(max_length=10, null=True, blank=True)

    ID_number = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.CharField(max_length=20, null=True, blank=True)
    savof_code = models.CharField(max_length=10, null=True, blank=True)
    
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    membership_expiry_date = models.DateField(null=True, blank=True)

    cell_number = models.CharField(max_length=20, null=True, blank=True)

    house_number = models.CharField(max_length=10, null=True, blank=True)
    street_name = models.CharField(max_length=100, null=True, blank=True)
    suburb = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True) 
    postal_code = models.CharField(max_length=10, null=True, blank=True)

    def is_active_member(self):
        if self.membership_type != "MEMBER":
            return False
        if not self.membership_expiry_date:
            return False
        return self.membership_expiry_date >= timezone.now().date()

    def __str__(self):
        return f"{self.user.email} Profile"

    def is_guest(self):
        return self.membership_type == "GUEST"


    def is_billable_as_member(self):
        return self.is_active_member()



