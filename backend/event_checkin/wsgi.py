"""
WSGI config for event_checkin project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "event_checkin.settings")

application = get_wsgi_application()
