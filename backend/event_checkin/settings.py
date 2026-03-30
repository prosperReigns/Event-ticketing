"""
Django settings for event_checkin project.
"""

from pathlib import Path

from decouple import config
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    raw = config(name, default=str(default))
    if isinstance(raw, bool):
        return raw
    normalized = str(raw).strip().lower()
    truthy = {"1", "true", "t", "yes", "y", "on", "debug", "development"}
    falsy = {"0", "false", "f", "no", "n", "off", "release", "production"}
    if normalized in truthy:
        return True
    if normalized in falsy:
        return False
    return default


DEBUG = env_bool("DEBUG", default=False)
SECRET_KEY = config("SECRET_KEY", default=get_random_secret_key())
ALLOWED_HOSTS = [
    host.strip()
    for host in config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")
    if host.strip()
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local apps
    "core",
    "events",
    "guests",
    "checkins",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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

# Database
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
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static & Media files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
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
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "120/min",
    },
}

# CORS / CSRF
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config(
        "CORS_ALLOWED_ORIGINS",
        default="http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config(
        "CSRF_TRUSTED_ORIGINS",
        default="http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# SendGrid
SENDGRID_API_KEY = config("SENDGRID_API_KEY", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@example.com")
SENDGRID_TIMEOUT_SECONDS = config("SENDGRID_TIMEOUT_SECONDS", default=10, cast=int)
SEND_EMAIL_ASYNC = env_bool("SEND_EMAIL_ASYNC", default=True)

# Brevo
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
TERMII_TIMEOUT_SECONDS = config("TERMII_TIMEOUT_SECONDS", default=10, cast=int)
