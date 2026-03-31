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
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
# Set explicitly in production to avoid trusting unintended origins.
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
# Allow cookies/CSRF tokens across the frontend origin only when explicitly enabled.
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", default=False)
if CORS_ALLOW_CREDENTIALS:
    # Cross-site cookies require SameSite=None + secure flags in production.
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"
