import os
import sys

sys.path.insert(0, "/home/appaquav/workflow_app")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "booking_project.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
