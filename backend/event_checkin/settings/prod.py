# prod.py
from .base import *
import dj_database_url
from decouple import config

# Core settings
DEBUG = False

SECRET_KEY = config("SECRET_KEY")

ALLOWED_HOSTS = [
    host.strip()
    for host in config("ALLOWED_HOSTS", default="").split(",")
    if host.strip()
]

# Database (Render PostgreSQL)
DATABASES = {
    "default": dj_database_url.config(default=config("DATABASE_URL"))
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# CORS
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config("CORS_ALLOWED_ORIGINS", default="").split(",")
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

# CSRF
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config("CSRF_TRUSTED_ORIGINS", default="").split(",")
    if origin.strip()
]
