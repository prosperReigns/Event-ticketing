"""
Email service using Brevo.

Provides a single public function:
    send_guest_qr_email(guest) -> bool
"""

import logging
import base64
import os
import html
import json
from urllib import request, error

from django.conf import settings
from django.utils import timezone

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
    html_content = _build_html_content(guest)
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
        qr_path = guest.qr_code_image.path
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


def _build_html_content(guest) -> str:
    event = guest.event
    checkin_url = f"{settings.CHECKIN_DOMAIN.rstrip('/')}/checkin/?token={guest.unique_token}"
    safe_guest_name = html.escape(guest.name)
    safe_event_name = html.escape(event.name)
    safe_event_location = html.escape(event.location)
    safe_table_number = html.escape(guest.table_number)
    safe_checkin_url = html.escape(checkin_url, quote=True)

    qr_html = ""
    qr_data_uri = _build_qr_data_uri(guest)
    if qr_data_uri:
        safe_qr_data_uri = html.escape(qr_data_uri, quote=True)
        qr_html = (
            f'<img src="{safe_qr_data_uri}" alt="QR code" '
            'style="width:200px; height:200px;" />'
        )

    event_time = timezone.localtime(event.start_datetime)

    return f"""
    <html>
      <body>
        <h2>Hello {safe_guest_name},</h2>
        <p>You are invited to <strong>{safe_event_name}</strong>.</p>
        <ul>
          <li><strong>Location:</strong> {safe_event_location}</li>
          <li><strong>Date &amp; Time:</strong> {event_time.strftime('%B %d, %Y at %I:%M %p %Z')}</li>
          <li><strong>Table Number:</strong> {safe_table_number}</li>
        </ul>
        <p>Please present the QR code below (or attached) at the entrance:</p>
        <div>{qr_html}</div>
        <p>Or use this link: <a href="{safe_checkin_url}">{safe_checkin_url}</a></p>
        <p>We look forward to seeing you!</p>
      </body>
    </html>
    """


def _build_qr_data_uri(guest) -> str:
    if not guest.qr_code_image:
        return ""
    qr_path = getattr(guest.qr_code_image, "path", "")
    if not qr_path or not os.path.exists(qr_path):
        return ""
    with open(qr_path, "rb") as file_obj:
        encoded = base64.b64encode(file_obj.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
