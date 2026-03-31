"""
SMS service using BulkSMS Nigeria with a provider pattern.
"""

import json
import logging
import re
from typing import Iterable, Optional
from urllib import error, request

from django.conf import settings

logger = logging.getLogger(__name__)

BULKSMS_SANDBOX_URL = "https://www.bulksmsnigeria.com/api/sandbox/v2/sms"
BULKSMS_PRODUCTION_URL = "https://www.bulksmsnigeria.com/api/v2/sms"


class SMSProvider:
    def send_sms(self, phone_number: str, message: str) -> bool:
        raise NotImplementedError

    def send_bulk_sms(self, phone_numbers: Iterable[str], message: str) -> bool:
        raise NotImplementedError


class BulkSMSProvider(SMSProvider):
    def __init__(self, sender_id: str, use_sandbox: bool) -> None:
        self.sender_id = sender_id
        self.url = BULKSMS_SANDBOX_URL if use_sandbox else BULKSMS_PRODUCTION_URL

    def send_sms(self, phone_number: str, message: str) -> bool:
        payload = {"from": self.sender_id, "to": phone_number, "body": message}
        return _send_bulksms_request(payload, self.url)

    def send_bulk_sms(self, phone_numbers: Iterable[str], message: str) -> bool:
        numbers = list(phone_numbers)
        if not numbers:
            logger.warning("No recipients provided for BulkSMS bulk send.")
            return False

        success_count = 0
        for phone_number in numbers:
            payload = {"from": self.sender_id, "to": phone_number, "body": message}
            success = _send_bulksms_request(payload, self.url)
            if success:
                success_count += 1

        if success_count == len(numbers):
            logger.info("BulkSMS bulk send succeeded for %s recipients.", len(numbers))
            return True

        logger.warning(
            "BulkSMS bulk send completed with %s/%s successes.",
            success_count,
            len(numbers),
        )
        return False


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _get_sms_provider() -> Optional[SMSProvider]:
    provider_name = getattr(settings, "SMS_PROVIDER", "bulksms").lower()
    if provider_name != "bulksms":
        logger.warning("Unsupported SMS provider '%s'.", provider_name)
        return None
    if not settings.BULKSMS_API_TOKEN or not settings.BULKSMS_SENDER_ID:
        logger.warning("BulkSMS settings are not configured; skipping SMS.")
        return None
    return BulkSMSProvider(settings.BULKSMS_SENDER_ID, use_sandbox=settings.DEBUG)


def _get_timeout_seconds() -> int:
    return getattr(settings, "BULKSMS_TIMEOUT_SECONDS", 10)


def _send_bulksms_request(payload: dict, url: str) -> bool:
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {settings.BULKSMS_API_TOKEN}",
    }
    req = request.Request(url, data=data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=_get_timeout_seconds()) as response:
            response_body = response.read().decode()
            logger.debug("BulkSMS response received (%s bytes).", len(response_body))
            if 200 <= response.status < 300:
                logger.info("BulkSMS request succeeded (status %s).", response.status)
                return True
            logger.error("BulkSMS returned status %s for request to %s", response.status, url)
            return False
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.exception("Failed to call BulkSMS (%s): %s", url, exc)
        return False


def send_rsvp_sms(guest, rsvp_url: str) -> bool:
    """Send an RSVP link SMS to the guest via BulkSMS Nigeria."""
    if not guest.phone:
        logger.warning("Guest %s has no phone number; skipping RSVP SMS.", guest.id)
        return False

    provider = _get_sms_provider()
    if not provider:
        return False

    normalized_phone = _normalize_phone(guest.phone or "")
    if not normalized_phone:
        logger.warning("Guest %s phone could not be normalized; skipping RSVP SMS.", guest.id)
        return False

    message = f"Hi {guest.name}, please RSVP here: {rsvp_url}"
    success = provider.send_sms(normalized_phone, message)
    if success:
        logger.info("RSVP SMS sent for guest %s", guest.id)
    else:
        logger.error("Failed to send RSVP SMS for guest %s", guest.id)
    return success


def send_whatsapp_message(
    guest,
    message: str,
    media_url: Optional[str] = None,
    media_caption: Optional[str] = None,
) -> bool:
    """BulkSMS Nigeria does not support WhatsApp messaging."""
    logger.warning(
        "WhatsApp messaging is not supported by the BulkSMS provider (guest %s).",
        guest.id,
    )
    return False


def send_bulk_sms(phone_numbers: Iterable[str], message: str) -> bool:
    """Send a bulk SMS message via BulkSMS Nigeria."""
    numbers = [_normalize_phone(value) for value in phone_numbers]
    numbers = [value for value in numbers if value]

    if not numbers:
        logger.warning("No valid phone numbers provided for bulk SMS.")
        return False

    provider = _get_sms_provider()
    if not provider:
        return False

    success = provider.send_bulk_sms(numbers, message)
    if success:
        logger.info("BulkSMS messages sent successfully (%s recipients).", len(numbers))
    else:
        logger.error("BulkSMS bulk send completed with failures.")
    return success
