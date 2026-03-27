"""
Check-in service.

Validates a QR token and performs the check-in flow.
"""

import logging
from typing import Dict, Any, Optional

from django.utils import timezone
from rest_framework import status

from guests.models import Guest
from checkins.models import CheckInLog

logger = logging.getLogger(__name__)


def process_checkin(token: str, user=None) -> Dict[str, Any]:
    """
    Execute the full check-in validation flow for *token*.

    Returns a dict with:
        success (bool)
        data    (dict)  – populated on success
        error   (str)   – populated on failure
        status_code (int)
    """
    # 1. Find guest by token
    try:
        guest = Guest.objects.select_related("event").get(unique_token=token)
    except Guest.DoesNotExist:
        return {
            "success": False,
            "error": "Invalid QR code. Guest not found.",
            "status_code": status.HTTP_404_NOT_FOUND,
        }

    event = guest.event

    # 2. Check event has started (timezone-aware)
    now = timezone.now()
    if now < event.start_datetime:
        return {
            "success": False,
            "error": "QR code not active yet. The event has not started.",
            "status_code": status.HTTP_400_BAD_REQUEST,
        }

    # 3. Duplicate check-in guard
    if guest.has_checked_in:
        return {
            "success": False,
            "error": "Guest already checked in.",
            "status_code": status.HTTP_409_CONFLICT,
        }

    # 4. Mark guest as checked in
    guest.has_checked_in = True
    guest.check_in_time = now
    guest.save(update_fields=["has_checked_in", "check_in_time"])

    # 5. Create audit log
    CheckInLog.objects.create(guest=guest, scanned_by=user)

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
