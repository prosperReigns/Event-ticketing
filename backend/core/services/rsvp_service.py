"""
RSVP service helpers.
"""

from django.conf import settings


def build_rsvp_url(guest) -> str:
    base = settings.RSVP_DOMAIN.rstrip("/")
    return f"{base}/rsvp/{guest.unique_token}/"
