from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)   # ✅ FIXED LINE

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Profile(models.Model):

    MEMBERSHIP_CHOICES = [
        ("guest", "Guest"),
        ("member", "Member"),
        ("expired", "Expired Member"),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_CHOICES,
        default="guest"
    )

    savof_code = models.CharField(max_length=50, blank=True, null=True)
    membership_expiry = models.DateField(blank=True, null=True)

    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def is_active_member(self):
        if self.membership_type != "member":
            return False
        if self.membership_expiry and self.membership_expiry < timezone.now().date():
            return False
        return True

    def __str__(self):
        return f"{self.user.email} Profile"
