"""
ASGI config for event_checkin project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "event_checkin.settings")

application = get_asgi_application()
