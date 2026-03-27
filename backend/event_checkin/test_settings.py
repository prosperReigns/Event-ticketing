"""
Test-specific settings – overrides the production database to use SQLite.
"""
from event_checkin.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Suppress real email calls
SENDGRID_API_KEY = ""

# Point media to /tmp
MEDIA_ROOT = "/tmp/test_media"
