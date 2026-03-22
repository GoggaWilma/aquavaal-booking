from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create or reset admin user'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        user, created = User.objects.get_or_create(
            email='admin@aquavaal.co.za'
        )

        user.set_password('Admin123!')
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS('Admin created'))
        else:
            self.stdout.write(self.style.SUCCESS('Admin password reset'))
