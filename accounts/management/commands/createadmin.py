from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create default admin user'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        if not User.objects.filter(email='admin@aquavaal.co.za').exists():
            User.objects.create_superuser(
                email='admin@aquavaal.co.za',
                password='Admin123!'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        else:
            self.stdout.write('Admin already exists')
