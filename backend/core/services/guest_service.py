"""
Guest service.

Handles business logic for creating guests, generating QR codes, and
sending invitation emails.
"""

import logging
from typing import List, Dict, Tuple

from guests.models import Guest
from events.models import Event
from .qr_service import generate_qr_code
from .email_service import send_guest_qr_email

logger = logging.getLogger(__name__)


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
        email = data.get("email", "").strip().lower()

        # Duplicate email check
        if Guest.objects.filter(event=event, email=email).exists():
            errors.append({"email": email, "error": "Guest with this email already exists for the event."})
            continue

        try:
            guest = Guest.objects.create(
                event=event,
                name=data["name"].strip(),
                email=email,
                phone=data.get("phone", ""),
                table_number=str(data["table_number"]),
            )

            # Generate QR code image
            try:
                generate_qr_code(guest)
            except Exception as exc:  # noqa: BLE001
                logger.exception("QR generation failed for guest %s: %s", guest.id, exc)

            # Send invitation email
            try:
                send_guest_qr_email(guest)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Email sending failed for guest %s: %s", guest.id, exc)

            created.append(guest)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to create guest with email %s: %s", email, exc)
            errors.append({"email": email, "error": str(exc)})

    return created, errors
