"""
Tests for the Event Guest QR Check-in System.

Uses SQLite in-memory DB for speed; no real SendGrid/email calls.
"""

import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from events.models import Event
from guests.models import Guest
from checkins.models import CheckInLog
from core.services.checkin_service import process_checkin
from core.services.guest_service import bulk_create_guests

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_event(name="Test Event", offset_hours=-1, is_active=True):
    """Create an Event that started *offset_hours* ago (default: 1 h ago)."""
    now = timezone.now()
    return Event.objects.create(
        name=name,
        location="Test Venue",
        start_datetime=now + timedelta(hours=offset_hours),
        is_active=is_active,
    )


def make_guest(event, name="Alice", email="alice@example.com", table="T1"):
    return Guest.objects.create(
        event=event,
        name=name,
        email=email,
        table_number=table,
    )


# ---------------------------------------------------------------------------
# Model / creation tests
# ---------------------------------------------------------------------------

class GuestCreationTest(TestCase):
    def test_guest_has_unique_token_on_create(self):
        event = make_event()
        guest = make_guest(event)
        self.assertIsNotNone(guest.unique_token)
        self.assertIsInstance(guest.unique_token, uuid.UUID)

    def test_guests_have_distinct_tokens(self):
        event = make_event()
        g1 = make_guest(event, name="Alice", email="alice@example.com")
        g2 = make_guest(event, name="Bob", email="bob@example.com")
        self.assertNotEqual(g1.unique_token, g2.unique_token)

    def test_duplicate_email_per_event_raises(self):
        from django.db import IntegrityError
        event = make_event()
        make_guest(event)
        with self.assertRaises(IntegrityError):
            make_guest(event)  # same email, same event → should fail


# ---------------------------------------------------------------------------
# QR Code tests
# ---------------------------------------------------------------------------

@override_settings(CHECKIN_DOMAIN="http://testserver", MEDIA_ROOT="/tmp/test_media")
class QRCodeGenerationTest(TestCase):
    def test_generate_qr_creates_image_file(self):
        import os
        import shutil
        from core.services.qr_service import generate_qr_code

        os.makedirs("/tmp/test_media/qr_codes", exist_ok=True)
        event = make_event()
        guest = make_guest(event)

        generate_qr_code(guest)
        guest.refresh_from_db()

        self.assertTrue(bool(guest.qr_code_image))
        self.assertTrue(guest.qr_code_image.name.endswith(".png"))

        # Cleanup
        shutil.rmtree("/tmp/test_media", ignore_errors=True)


# ---------------------------------------------------------------------------
# Check-in service tests
# ---------------------------------------------------------------------------

class CheckInServiceTest(TestCase):
    def setUp(self):
        self.event = make_event()  # started 1 h ago
        self.guest = make_guest(self.event)

    def test_successful_checkin(self):
        result = process_checkin(str(self.guest.unique_token))
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["guest_name"], "Alice")
        self.assertEqual(result["data"]["event_name"], "Test Event")

    def test_checkin_marks_guest_checked_in(self):
        process_checkin(str(self.guest.unique_token))
        self.guest.refresh_from_db()
        self.assertTrue(self.guest.has_checked_in)
        self.assertIsNotNone(self.guest.check_in_time)

    def test_checkin_creates_log_entry(self):
        process_checkin(str(self.guest.unique_token))
        self.assertEqual(CheckInLog.objects.filter(guest=self.guest).count(), 1)

    def test_invalid_token_returns_404(self):
        result = process_checkin(str(uuid.uuid4()))
        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 404)

    def test_duplicate_checkin_rejected(self):
        process_checkin(str(self.guest.unique_token))  # first check-in
        result = process_checkin(str(self.guest.unique_token))  # duplicate
        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 409)
        self.assertIn("already checked in", result["error"])

    def test_early_scan_rejected(self):
        # Event starts 2 hours in the future
        future_event = make_event(name="Future Event", offset_hours=2)
        guest = make_guest(future_event, name="Bob", email="bob@example.com")
        result = process_checkin(str(guest.unique_token))
        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 400)
        self.assertIn("not active yet", result["error"])


# ---------------------------------------------------------------------------
# Bulk guest creation tests
# ---------------------------------------------------------------------------

@patch("core.services.guest_service.generate_qr_code")
@patch("core.services.guest_service.send_guest_qr_email")
class BulkGuestCreationTest(TestCase):
    def setUp(self):
        self.event = make_event()

    def test_bulk_create_returns_created_list(self, mock_email, mock_qr):
        data = [
            {"name": "Alice", "email": "alice@example.com", "table_number": "T1"},
            {"name": "Bob", "email": "bob@example.com", "table_number": "T2"},
        ]
        created, errors = bulk_create_guests(self.event, data)
        self.assertEqual(len(created), 2)
        self.assertEqual(len(errors), 0)

    def test_duplicate_email_goes_to_errors(self, mock_email, mock_qr):
        make_guest(self.event)  # alice already exists
        data = [{"name": "Alice2", "email": "alice@example.com", "table_number": "T1"}]
        created, errors = bulk_create_guests(self.event, data)
        self.assertEqual(len(created), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("already exists", errors[0]["error"])

    def test_qr_generation_called_per_guest(self, mock_email, mock_qr):
        data = [
            {"name": "Alice", "email": "alice@example.com", "table_number": "T1"},
        ]
        bulk_create_guests(self.event, data)
        mock_qr.assert_called_once()

    def test_email_sent_per_guest(self, mock_email, mock_qr):
        data = [
            {"name": "Alice", "email": "alice@example.com", "table_number": "T1"},
        ]
        bulk_create_guests(self.event, data)
        mock_email.assert_called_once()
