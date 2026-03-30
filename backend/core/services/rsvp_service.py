"""
RSVP service helpers.
"""

from django.conf import settings


def build_rsvp_url(guest) -> str:
    """Construct the RSVP URL for a guest using the configured domain."""
    base = settings.RSVP_DOMAIN.rstrip("/")
    return f"{base}/rsvp/{guest.unique_token}/"
