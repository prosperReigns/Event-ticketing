from .base import *
from django.core.management.utils import get_random_secret_key

DEBUG = True
SECRET_KEY = config("SECRET_KEY", default="")
if not SECRET_KEY:
    # Use a generated key for local development only.
    SECRET_KEY = get_random_secret_key()
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
CORS_ALLOW_CREDENTIALS = True  # Dev frontend uses cookies/CSRF tokens across ports.

# Disable request throttling in dev/test so automated tests don't hit 429 errors.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}

db_name = config("DATABASE_NAME", default="")
if db_name:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": config("DATABASE_USER", default=""),
            "PASSWORD": config("DATABASE_PASSWORD", default=""),
            "HOST": config("DATABASE_HOST", default="localhost"),
            "PORT": config("DATABASE_PORT", default="5432"),
        }
    }
else:
    # Fall back to local SQLite to keep dev/test environments working.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
