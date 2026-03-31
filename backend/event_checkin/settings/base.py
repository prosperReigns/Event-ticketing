# base.py
from pathlib import Path
from decouple import config
from django.core.management.utils import get_random_secret_key
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Functions
def env_bool(name: str, default: bool = False) -> bool:
    raw = config(name, default=str(default))
    truthy = {"1", "true", "t", "yes", "y", "on", "debug", "development"}
    falsy = {"0", "false", "f", "no", "n", "off", "release", "production"}
    if str(raw).strip().lower() in truthy:
        return True
    if str(raw).strip().lower() in falsy:
        return False
    return default


def env_list(name: str, default: str = "") -> list[str]:
    raw = config(name, default=default)
    return [item.strip() for item in str(raw).split(",") if item.strip()]


ALLOWED_HOSTS = [
    host.strip()
    for host in config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")
    if host.strip()
]
render_host = config("RENDER_EXTERNAL_HOSTNAME", default="").strip()
if render_host:
    # Render sets this env var; adding it avoids DisallowedHost 400s.
    ALLOWED_HOSTS.append(render_host)

# Installed apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    # Local apps
    "core",
    "events",
    "guests",
    "checkins",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Keep early in the stack for 4xx CORS headers.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "event_checkin.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "event_checkin.wsgi.application"

# Static & media files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="Africa/Lagos")
USE_I18N = True
USE_TZ = True

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "30/min", "user": "120/min"},
}

# CORS / CSRF defaults (override in dev/prod as needed)
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
)
_csrf_trusted_origins = env_list("CSRF_TRUSTED_ORIGINS")
if not _csrf_trusted_origins:
    _csrf_trusted_origins = CORS_ALLOWED_ORIGINS
CSRF_TRUSTED_ORIGINS = _csrf_trusted_origins
# Only allow credentials when explicitly enabled for cross-site requests.
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", default=False)

# Email / 3rd party integrations can stay here
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@example.com")
SEND_EMAIL_ASYNC = env_bool("SEND_EMAIL_ASYNC", default=True)
BREVO_API_KEY = config("BREVO_API_KEY", default="")
BREVO_SENDER_EMAIL = config("BREVO_SENDER_EMAIL", default=DEFAULT_FROM_EMAIL)
BREVO_SENDER_NAME = config("BREVO_SENDER_NAME", default="")
BREVO_TIMEOUT_SECONDS = config("BREVO_TIMEOUT_SECONDS", default=10, cast=int)
BREVO_EMAIL_URL = config(
    "BREVO_EMAIL_URL", default="https://api.brevo.com/v3/smtp/email"
)

# QR Code / domain for check-in URL
CHECKIN_DOMAIN = config("CHECKIN_DOMAIN", default="http://127.0.0.1:8000")
RSVP_DOMAIN = config("RSVP_DOMAIN", default=CHECKIN_DOMAIN)

# Termii
TERMII_API_KEY = config("TERMII_API_KEY", default="")
TERMII_SENDER_ID = config("TERMII_SENDER_ID", default="")
TERMII_BASE_URL = config("TERMII_BASE_URL", default="https://api.ng.termii.com")
TERMII_SMS_SEND_URL = config("TERMII_SMS_SEND_URL", default="")
TERMII_SMS_BULK_URL = config("TERMII_SMS_BULK_URL", default="")
TERMII_TIMEOUT_SECONDS = config("TERMII_TIMEOUT_SECONDS", default=10, cast=int)

# BulkSMS Nigeria
BULKSMS_API_TOKEN = config("BULKSMS_API_TOKEN", default="")
BULKSMS_SENDER_ID = config("BULKSMS_SENDER_ID", default="")
SMS_PROVIDER = config("SMS_PROVIDER", default="bulksms")
