# __init__.py
import os

env = os.getenv("DJANGO_ENV", "dev")

if env == "prod":
    from .prod import *
else:
    from .dev import *

from django.core.exceptions import ImproperlyConfigured

if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY must be set in the selected settings.")
