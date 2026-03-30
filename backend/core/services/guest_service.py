"""
Guest service.

Handles business logic for creating guests, generating QR codes, and
sending invitation emails.
"""

import logging
import threading
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from events.models import Event
from guests.models import Guest

from .email_service import send_guest_qr_email
from .qr_service import generate_qr_code
from .rsvp_service import build_rsvp_url
from .sms_service import send_rsvp_sms

logger = logging.getLogger(__name__)


def _send_email_async(guest_id: str) -> None:
    try:
        close_old_connections()
        guest = Guest.objects.select_related("event").get(id=guest_id)
        send_guest_qr_email(guest)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Async email sending failed for guest %s: %s", guest_id, exc)
    finally:
        close_old_connections()


def _normalize_email(raw_email: Optional[str]) -> Optional[str]:
    if raw_email is None:
        return None
    normalized = str(raw_email).strip().lower()
    return normalized or None


def bulk_create_guests(
    event: Event, guest_data_list: List[Dict]
) -> Tuple[List[Guest], List[Dict]]:
    """
    Create multiple guests for *event*.

    For each entry in *guest_data_list*:
    - validate uniqueness (email per event)
    - create Guest
    - generate QR code
    - send invitation email

    Returns (created_guests, errors) where errors is a list of dicts
    describing any skipped entries.
    """
    created: List[Guest] = []
    errors: List[Dict] = []

    for data in guest_data_list:
        name = str(data.get("name", "")).strip()
        email = _normalize_email(data.get("email"))
        table_number = str(data.get("table_number", "")).strip()
        phone = str(data.get("phone", "")).strip()

        if not name:
            errors.append(
                {
                    "email": email or None,
                    "error": "Each guest must include a name.",
                }
            )
            continue
        if not email and not phone:
            errors.append(
                {
                    "email": None,
                    "error": "Each guest must include an email or phone number.",
                }
            )
            continue

        if len(phone) > 30:
            errors.append(
                {
                    "email": email,
                    "error": "Phone number cannot exceed 30 characters.",
                }
            )
            continue

        # Duplicate email check
        if email and Guest.objects.filter(event=event, email__iexact=email).exists():
            errors.append(
                {
                    "email": email,
                    "error": "Guest with this email already exists for the event.",
                }
            )
            continue

        try:
            is_placeholder = not bool(email)
            rsvp_status = (
                Guest.RSVP_STATUS_PENDING
                if is_placeholder
                else Guest.RSVP_STATUS_ATTENDING
            )
            rsvp_time = None if is_placeholder else timezone.now()
            guest = Guest.objects.create(
                event=event,
                name=name,
                email=email,
                phone=phone,
                table_number=table_number,
                is_placeholder=is_placeholder,
                rsvp_status=rsvp_status,
                rsvp_time=rsvp_time,
            )

            if is_placeholder:
                try:
                    rsvp_url = build_rsvp_url(guest)
                    send_rsvp_sms(guest, rsvp_url)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("RSVP SMS sending failed for guest %s: %s", guest.id, exc)
            else:
                # Generate QR code image
                try:
                    generate_qr_code(guest)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("QR generation failed for guest %s: %s", guest.id, exc)

                # Send invitation email
                try:
                    if settings.SEND_EMAIL_ASYNC:
                        thread = threading.Thread(
                            target=_send_email_async,
                            args=(str(guest.id),),
                            daemon=True,
                        )
                        thread.start()
                    else:
                        send_guest_qr_email(guest)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Email sending failed for guest %s: %s", guest.id, exc)

            created.append(guest)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to create guest with email %s: %s", email, exc)
            errors.append(
                {
                    "email": email,
                    "error": "Guest could not be created due to a server error.",
                }
            )

    return created, errors
