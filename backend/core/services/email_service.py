"""
Email service using Brevo.

Provides a single public function:
    send_guest_qr_email(guest) -> bool
"""

import logging
import base64
import os
import json
from urllib.parse import urlencode, urljoin, urlparse
from urllib import request, error

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from .rsvp_service import build_rsvp_url

logger = logging.getLogger(__name__)


def send_guest_qr_email(guest) -> bool:
    """
    Send the QR-code invitation email to *guest*.

    Returns True on success, False on failure (logs the error).
    """
    if not guest.email:
        logger.warning("Guest %s has no email; skipping invitation.", guest.id)
        return False

    if not settings.BREVO_API_KEY:
        logger.warning("Brevo is not configured; skipping email for %s", guest.email)
        return False

    return _send_brevo_email(guest)


def _send_brevo_email(guest) -> bool:
    logo_src = _resolve_image_url(guest.event.logo)
    qr_src = _resolve_image_url(guest.qr_code_image)

    html_content = _build_html_content(guest, logo_src=logo_src, qr_src=qr_src)
    payload = {
        "sender": {
            "email": settings.BREVO_SENDER_EMAIL,
            "name": settings.BREVO_SENDER_NAME or settings.BREVO_SENDER_EMAIL,
        },
        "to": [{"email": guest.email, "name": guest.name}],
        "subject": f"Your Invitation to {guest.event.name}",
        "htmlContent": html_content,
    }

    if guest.qr_code_image:
        qr_path = _resolve_field_path(guest.qr_code_image)
        if os.path.exists(qr_path):
            with open(qr_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            payload["attachment"] = [{"content": encoded, "name": "qr_code.png"}]

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "api-key": settings.BREVO_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json",
    }
    req = request.Request(settings.BREVO_EMAIL_URL, data=data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=settings.BREVO_TIMEOUT_SECONDS) as response:
            if response.status in (200, 201, 202):
                logger.info("Brevo email sent to %s (status %s)", guest.email, response.status)
                return True
            logger.error("Brevo returned status %s for %s", response.status, guest.email)
            return False
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.exception("Failed to send Brevo email to %s: %s", guest.email, exc)
        return False


def _build_html_content(guest, logo_src: str = "", qr_src: str = "") -> str:
    event = guest.event
    event_time = timezone.localtime(event.start_datetime)
    event_time_display = event_time.strftime("%B %d, %Y at %I:%M %p %Z")
    checkin_url = _build_checkin_url(guest)
    rsvp_url = build_rsvp_url(guest)

    resolved_logo_src = logo_src or _resolve_image_url(event.logo)
    resolved_qr_src = qr_src or _resolve_image_url(guest.qr_code_image)

    return render_to_string(
        "emails/guest_invitation.html",
        {
            "guest_name": guest.name,
            "event_name": event.name,
            "event_location": event.location,
            "table_number": guest.table_number,
            "event_time_display": event_time_display,
            "logo_src": resolved_logo_src,
            "qr_src": resolved_qr_src,
            "checkin_url": checkin_url,
            "rsvp_url": rsvp_url,
        },
    )


def _build_checkin_url(guest) -> str:
    base = settings.CHECKIN_DOMAIN.rstrip("/")
    query = urlencode({"token": str(guest.unique_token)})
    return f"{base}/checkin/?{query}"


def _resolve_field_path(image_field) -> str:
    try:
        return image_field.path
    except (AttributeError, ValueError, OSError):
        return ""


def _resolve_image_url(image_field) -> str:
    if not image_field:
        return ""
    try:
        image_url = image_field.url
    except (AttributeError, ValueError):
        return ""
    if not image_url:
        return ""
    if urlparse(image_url).scheme in {"http", "https"}:
        return image_url

    base = settings.CHECKIN_DOMAIN.rstrip("/")
    if not base:
        return image_url
    if image_url.startswith("/"):
        return f"{base}{image_url}"
    return urljoin(f"{base}/", image_url)
