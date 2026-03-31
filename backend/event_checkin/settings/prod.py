# prod.py
from .base import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in config("ALLOWED_HOSTS").split(",")]

# Database (PostgreSQL on Render)
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
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in config("CORS_ALLOWED_ORIGINS", default="").split(",") if origin.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in config("CSRF_TRUSTED_ORIGINS", default="").split(",") if origin.strip()]