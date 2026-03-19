from django.db import models


class Stand(models.Model):

    SECTION_CHOICES = [
        ('ESKOM', 'Eskom'),
        ('BOAT', 'Boat Club'),
        ('OWNER', 'Owner Managed'),
        ('PUBLIC', 'Public'),
    ]

    APPROVAL_FLOW_CHOICES = [
        ('ESKOM_ADMIN', 'Eskom → Admin'),
        ('BOAT_ADMIN', 'Boat Club → Admin'),
        ('OWNER_ADMIN', 'Owner → Admin'),
        ('ADMIN_ONLY', 'Admin Only'),
    ]

    number = models.PositiveIntegerField(unique=True)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    approval_flow = models.CharField(max_length=20, choices=APPROVAL_FLOW_CHOICES)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Stand {self.number}"
