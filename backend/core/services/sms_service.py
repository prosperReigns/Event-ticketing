"""
SMS service using Termii.
"""

import json
import logging
from urllib import request, error

from django.conf import settings

logger = logging.getLogger(__name__)


def send_rsvp_sms(guest, rsvp_url: str) -> bool:
    if not guest.phone:
        logger.warning("Guest %s has no phone number; skipping RSVP SMS.", guest.id)
        return False
    if not settings.TERMII_API_KEY or not settings.TERMII_SENDER_ID:
        logger.warning("TERMII settings are not configured; skipping RSVP SMS to %s", guest.phone)
        return False

    payload = {
        "api_key": settings.TERMII_API_KEY,
        "to": guest.phone,
        "from": settings.TERMII_SENDER_ID,
        "sms": (
            f"Hi {guest.name}, please RSVP for {guest.event.name} using this link: {rsvp_url}"
        ),
        "type": "plain",
        "channel": "generic",
    }

    data = json.dumps(payload).encode("utf-8")
    url = f"{settings.TERMII_BASE_URL.rstrip('/')}/api/sms/send"
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    req = request.Request(url, data=data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=settings.TERMII_TIMEOUT_SECONDS) as response:
            if response.status in (200, 201, 202):
                logger.info("RSVP SMS sent to %s (status %s)", guest.phone, response.status)
                return True
            logger.error("Termii returned status %s for %s", response.status, guest.phone)
            return False
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.exception("Failed to send RSVP SMS to %s: %s", guest.phone, exc)
        return False
