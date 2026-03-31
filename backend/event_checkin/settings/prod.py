# prod.py
from .base import *
import dj_database_url

DEBUG = False
SECRET_KEY = config("SECRET_KEY")
ALLOWED_HOSTS = [host.strip() for host in config("ALLOWED_HOSTS").split(",") if host.strip()]
render_host = config("RENDER_EXTERNAL_HOSTNAME", default="").strip()
if render_host:
    # Render provides the external hostname so we can avoid DisallowedHost 400s.
    ALLOWED_HOSTS.append(render_host)

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
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS") or CORS_ALLOWED_ORIGINS
# Allow cookies/CSRF tokens across the frontend origin when using session auth.
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", default=True)
if CORS_ALLOW_CREDENTIALS:
    # Cross-site cookies require SameSite=None + secure flags in production.
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"
