"""
Test-specific settings that override runtime settings for deterministic tests.
"""
from pathlib import Path

from event_checkin.settings import *  # noqa: F401, F403

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Suppress real email calls
BREVO_API_KEY = ""
SEND_EMAIL_ASYNC = False

# Point media to a workspace-local temp directory for cross-platform compatibility.
MEDIA_ROOT = BASE_DIR / "test_media"

# Disable throttling in tests to avoid intermittent 429 failures.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}
