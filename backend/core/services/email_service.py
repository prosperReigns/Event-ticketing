"""
Email service using Brevo (primary) with SendGrid fallback.

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

logger = logging.getLogger(__name__)


def send_guest_qr_email(guest) -> bool:
    """
    Send the QR-code invitation email to *guest*.

    Returns True on success, False on failure (logs the error).
    """
    if not guest.email:
        logger.warning("Guest %s has no email; skipping invitation.", guest.id)
        return False

    if settings.BREVO_API_KEY:
        return _send_brevo_email(guest)

    return _send_sendgrid_email(guest)


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
            payload["attachments"] = [{"content": encoded, "name": "qr_code.png"}]

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


def _send_sendgrid_email(guest) -> bool:
    """Send the invitation email via SendGrid as a fallback provider."""
    api_key = settings.SENDGRID_API_KEY
    if not api_key:
        logger.warning("Email providers not configured – skipping email for %s", guest.email)
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import (
            Mail,
            Attachment,
            FileContent,
            FileName,
            FileType,
            Disposition,
            ContentId,
        )

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        sg.client.timeout = settings.SENDGRID_TIMEOUT_SECONDS

        html_content = _build_html_content(guest)

        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=guest.email,
            subject=f"Your Invitation to {guest.event.name}",
            html_content=html_content,
        )

        # Attach QR code image if available
        if guest.qr_code_image:
            qr_path = guest.qr_code_image.path
            if os.path.exists(qr_path):
                with open(qr_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()

                attachment = Attachment(
                    FileContent(encoded),
                    FileName("qr_code.png"),
                    FileType("image/png"),
                    Disposition("inline"),
                    ContentId("QRCode"),
                )
                message.attachment = attachment

        response = sg.send(message)
        if response.status_code in (200, 202):
            logger.info("QR email sent to %s (status %s)", guest.email, response.status_code)
            return True

        logger.error(
            "SendGrid returned status %s for %s", response.status_code, guest.email
        )
        return False

    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send email to %s: %s", guest.email, exc)
        return False


def _build_html_content(guest) -> str:
    event = guest.event
    checkin_url = f"{settings.CHECKIN_DOMAIN}/api/checkin/{guest.unique_token}/"
    safe_guest_name = html.escape(guest.name)
    safe_event_name = html.escape(event.name)
    safe_event_location = html.escape(event.location)
    safe_table_number = html.escape(guest.table_number)
    safe_checkin_url = html.escape(checkin_url, quote=True)

    qr_html = ""
    if guest.qr_code_image:
        qr_html = '<img src="cid:QRCode" alt="QR code" style="width:200px; height:200px;" />'

    return f"""
    <html>
      <body>
        <h2>Hello {safe_guest_name},</h2>
        <p>You are invited to <strong>{safe_event_name}</strong>.</p>
        <ul>
          <li><strong>Location:</strong> {safe_event_location}</li>
          <li><strong>Date &amp; Time:</strong> {event.start_datetime.strftime('%B %d, %Y at %I:%M %p %Z')}</li>
          <li><strong>Table Number:</strong> {safe_table_number}</li>
        </ul>
        <p>Please present the QR code below (or attached) at the entrance:</p>
        <div>{qr_html}</div>
        <p>Or use this link: <a href="{safe_checkin_url}">{safe_checkin_url}</a></p>
        <p>We look forward to seeing you!</p>
      </body>
    </html>
    """
