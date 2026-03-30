"""
Check-in service.

Validates a QR token and performs the check-in flow.
"""

import logging
from typing import Any, Dict, Optional

from django.utils import timezone
from rest_framework import status
from django.db import transaction

from guests.models import Guest
from checkins.models import CheckInLog

logger = logging.getLogger(__name__)


def process_checkin(token: str, user: Optional[object] = None) -> Dict[str, Any]:
    """
    Execute the full check-in validation flow for *token*.

    Returns a dict with:
        success (bool)
        data    (dict)  – populated on success
        error   (str)   – populated on failure
        status_code (int)
    """
    try:
        with transaction.atomic():
            guest = (
                Guest.objects.select_for_update()
                .select_related("event")
                .get(unique_token=token)
            )
            event = guest.event
            now = timezone.now()

            # 1. Validate event timing and status
            if now < event.start_datetime:
                return {
                    "success": False,
                    "error": "QR code not active yet. The event has not started.",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                }

            if event.end_datetime and now > event.end_datetime:
                return {
                    "success": False,
                    "error": "Event has already ended.",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                }

            if not event.is_active:
                return {
                    "success": False,
                    "error": "Event is not active yet.",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                }

            # 2. Duplicate check-in guard
            if guest.has_checked_in:
                return {
                    "success": False,
                    "error": "Guest already checked in.",
                    "status_code": status.HTTP_409_CONFLICT,
                }

            # 3. Mark guest as checked in
            guest.has_checked_in = True
            guest.check_in_time = now
            guest.save(update_fields=["has_checked_in", "check_in_time"])

            # 4. Create audit log
            CheckInLog.objects.create(guest=guest, scanned_by=user)
    except Guest.DoesNotExist:
        return {
            "success": False,
            "error": "Invalid QR code. Guest not found.",
            "status_code": status.HTTP_404_NOT_FOUND,
        }

    logger.info("Guest %s checked in to event %s at %s", guest.name, event.name, now)

    return {
        "success": True,
        "data": {
            "guest_name": guest.name,
            "table_number": guest.table_number,
            "event_name": event.name,
            "check_in_time": guest.check_in_time,
            "message": f"Welcome, {guest.name}! You are checked in.",
        },
        "status_code": status.HTTP_200_OK,
    }
