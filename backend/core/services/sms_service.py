"""
SMS service using Termii.
"""

import json
import logging
import re
from typing import Iterable, Optional
from urllib import request, error

from django.conf import settings

logger = logging.getLogger(__name__)


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _build_termii_url(path_suffix: str, override_url: str) -> str:
    if override_url:
        return override_url
    base_url = settings.TERMII_BASE_URL.rstrip("/")
    if base_url.endswith("/api"):
        return f"{base_url}/{path_suffix.lstrip('/')}"
    return f"{base_url}/api/{path_suffix.lstrip('/')}"


def _send_termii_request(payload: dict, url: str, success_label: str) -> bool:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    req = request.Request(url, data=data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=settings.TERMII_TIMEOUT_SECONDS) as response:
            response_body = response.read().decode()
            logger.info("Termii response: %s", response_body)
            if response.status in (200, 201, 202):
                logger.info("%s (status %s)", success_label, response.status)
                return True
            logger.error("Termii returned status %s for request to %s", response.status, url)
            return False
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.exception("Failed to call Termii (%s): %s", url, exc)
        return False


def send_rsvp_sms(guest, rsvp_url: str) -> bool:
    """Send an RSVP link SMS to the guest via Termii."""
    if not guest.phone:
        logger.warning("Guest %s has no phone number; skipping RSVP SMS.", guest.id)
        return False
    if not settings.TERMII_API_KEY or not settings.TERMII_SENDER_ID:
        logger.warning("TERMII settings are not configured; skipping RSVP SMS to %s", guest.phone)
        return False

    normalized_phone = _normalize_phone(guest.phone or "")
    if not normalized_phone:
        logger.warning("Guest %s phone could not be normalized; skipping RSVP SMS.", guest.id)
        return False

    payload = {
        "api_key": settings.TERMII_API_KEY,
        "to": normalized_phone,
        "from": settings.TERMII_SENDER_ID,
        "sms": (
            f"Hi {guest.name}, please RSVP for {guest.event.name} using this link: {rsvp_url}"
        ),
        "type": "plain",
        "channel": "generic",
    }
    url = "https://v3.api.termii.com/api/sms/send"
    return _send_termii_request(
        payload,
        url,
        f"RSVP SMS sent to {guest.phone}",
    )


def send_whatsapp_message(
    guest,
    message: str,
    media_url: Optional[str] = None,
    media_caption: Optional[str] = None,
) -> bool:
    """Send a WhatsApp conversational message to the guest via Termii."""
    if not guest.phone:
        logger.warning("Guest %s has no phone number; skipping WhatsApp message.", guest.id)
        return False
    if not settings.TERMII_API_KEY or not settings.TERMII_SENDER_ID:
        logger.warning(
            "TERMII settings are not configured; skipping WhatsApp to %s", guest.phone
        )
        return False

    normalized_phone = _normalize_phone(guest.phone or "")
    if not normalized_phone:
        logger.warning(
            "Guest %s phone could not be normalized; skipping WhatsApp message.", guest.id
        )
        return False

    payload = {
        "api_key": settings.TERMII_API_KEY,
        "to": normalized_phone,
        "from": settings.TERMII_SENDER_ID,
        "type": "plain",
        "channel": "whatsapp",
    }

    if media_url:
        media_payload = {"url": media_url}
        if media_caption:
            media_payload["caption"] = media_caption
        payload["media"] = media_payload
    else:
        payload["sms"] = message

    url = _build_termii_url("sms/send", settings.TERMII_SMS_SEND_URL.strip())
    return _send_termii_request(
        payload,
        url,
        f"WhatsApp message sent to {guest.phone}",
    )


def send_bulk_sms(
    phone_numbers: Iterable[str],
    message: str,
    channel: str = "generic",
) -> bool:
    """Send a bulk SMS message via Termii."""
    numbers = [_normalize_phone(value) for value in phone_numbers]
    numbers = [value for value in numbers if value]

    if not numbers:
        logger.warning("No valid phone numbers provided for bulk SMS.")
        return False
    if len(numbers) > 100:
        logger.warning("Bulk SMS supports up to 100 phone numbers per request.")
        return False
    if channel not in {"generic", "dnd"}:
        logger.warning("Invalid bulk SMS channel '%s'; use 'generic' or 'dnd'.", channel)
        return False
    if not settings.TERMII_API_KEY or not settings.TERMII_SENDER_ID:
        logger.warning("TERMII settings are not configured; skipping bulk SMS.")
        return False

    payload = {
        "api_key": settings.TERMII_API_KEY,
        "to": numbers,
        "from": settings.TERMII_SENDER_ID,
        "sms": message,
        "type": "plain",
        "channel": channel,
    }

    url = _build_termii_url("sms/send/bulk", settings.TERMII_SMS_BULK_URL.strip())
    return _send_termii_request(payload, url, "Bulk SMS sent successfully")
