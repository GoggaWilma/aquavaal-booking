from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Stand(models.Model):
    number = models.IntegerField(unique=True)

    is_member_owned = models.BooleanField(default=False)

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    SECTION_CHOICES = [
        ('ESKOM', 'Eskom'),
        ('BOAT', 'Boat Club'),
        ('OWNER', 'Owner Managed'),
        ('PUBLIC', 'Public'),
    ]

    APPROVAL_FLOW_CHOICES = [
        ('ADMIN_ONLY', 'Admin Only'),
        ('ESKOM_ADMIN', 'Eskom → Admin'),
        ('BOAT_ADMIN', 'Boat Club → Admin'),
        ('OWNER_ADMIN', 'Owner → Admin'),
    ]

    number = models.PositiveIntegerField(unique=True)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    
    approval_flow = models.CharField(
        max_length=30,
        choices=APPROVAL_FLOW_CHOICES,
        default="ADMIN_ONLY"
    )

    def __str__(self):
        return f"Stand {self.number}"
