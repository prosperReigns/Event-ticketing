"""
Tests for the Event Guest QR Check-in System.

Uses SQLite in-memory DB for speed; no real email calls.
"""

import os
import uuid
from pathlib import Path
import tempfile
import shutil
from datetime import timedelta
from unittest.mock import patch
from io import BytesIO

from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.test import APIClient

from event_checkin.settings.base import env_list
from events.models import Event
from guests.models import Guest
from checkins.models import CheckInLog
from core.services.checkin_service import process_checkin
from core.services.guest_service import bulk_create_guests
from core.services.rsvp_service import build_rsvp_url
from core.services.email_service import _build_html_content
from core.services.qr_service import generate_qr_code, _load_event_logo
from PIL import Image

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


def make_guest(
    event,
    name="Alice",
    email="alice@example.com",
    table="T1",
    rsvp_status=Guest.RSVP_STATUS_ATTENDING,
    is_placeholder=False,
):
    return Guest.objects.create(
        event=event,
        name=name,
        email=email,
        table_number=table,
        rsvp_status=rsvp_status,
        is_placeholder=is_placeholder,
    )


class EnvListHelperTest(TestCase):
    def test_env_list_parses_csv(self):
        with patch.dict(os.environ, {"TEST_CSV": " a, b , ,c "}):
            self.assertEqual(env_list("TEST_CSV"), ["a", "b", "c"])

    def test_env_list_empty(self):
        with patch.dict(os.environ, {"TEST_EMPTY": ""}):
            self.assertEqual(env_list("TEST_EMPTY"), [])


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

TEST_MEDIA_ROOT = Path(tempfile.gettempdir()) / "event_checkin_test_media"


@override_settings(CHECKIN_DOMAIN="http://testserver", MEDIA_ROOT=str(TEST_MEDIA_ROOT))
class QRCodeGenerationTest(TestCase):
    def test_generate_qr_creates_image_file(self):
        import os
        import shutil
        from core.services.qr_service import generate_qr_code

        os.makedirs(TEST_MEDIA_ROOT / "qr_codes", exist_ok=True)
        event = make_event()
        guest = make_guest(event)

        generate_qr_code(guest)
        guest.refresh_from_db()

        self.assertTrue(bool(guest.qr_code_image))
        self.assertTrue(guest.qr_code_image.name.endswith(".png"))

        # Cleanup
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


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

    def test_pending_rsvp_rejected(self):
        pending_guest = make_guest(
            self.event,
            name="Pending Guest",
            email="pending@example.com",
            rsvp_status=Guest.RSVP_STATUS_PENDING,
        )
        result = process_checkin(str(pending_guest.unique_token))
        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 403)
        self.assertIn("not confirmed", result["error"])


# ---------------------------------------------------------------------------
# Bulk guest creation tests
# ---------------------------------------------------------------------------

@override_settings(SEND_EMAIL_ASYNC=False)
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

    def test_missing_table_number_is_allowed(self, mock_email, mock_qr):
        data = [
            {"name": "No Table Guest", "email": "notable@example.com"},
        ]
        created, errors = bulk_create_guests(self.event, data)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].table_number, "")


@patch("core.services.guest_service.send_rsvp_sms")
class RSVPGuestCreationTest(TestCase):
    def setUp(self):
        self.event = make_event()

    def test_rsvp_guest_creates_placeholder(self, mock_sms):
        data = [
            {"name": "RSVP Guest", "phone": "+1234567890"},
        ]
        created, errors = bulk_create_guests(self.event, data)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(created), 1)
        guest = created[0]
        self.assertTrue(guest.is_placeholder)
        self.assertEqual(guest.rsvp_status, Guest.RSVP_STATUS_PENDING)
        mock_sms.assert_called_once()


@override_settings(
    CHECKIN_DOMAIN="http://testserver",
    RSVP_DOMAIN="http://testserver",
    SECURE_SSL_REDIRECT=False,
)
@patch("guests.views.send_guest_qr_email")
@patch("guests.views.generate_qr_code")
class RSVPSubmissionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.event = make_event()
        self.guest = make_guest(
            self.event,
            name="RSVP Guest",
            email=None,
            rsvp_status=Guest.RSVP_STATUS_PENDING,
            is_placeholder=True,
        )

    def test_rsvp_submission_marks_attending(self, mock_qr, mock_email):
        response = self.client.post(
            f"/api/rsvp/{self.guest.unique_token}/",
            data={
                "name": "RSVP Guest",
                "email": "rsvp@example.com",
                "phone": "+1234567890",
                "rsvp_status": Guest.RSVP_STATUS_ATTENDING,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.guest.refresh_from_db()
        self.assertEqual(self.guest.rsvp_status, Guest.RSVP_STATUS_ATTENDING)
        self.assertFalse(self.guest.is_placeholder)
        mock_qr.assert_called_once()
        mock_email.assert_called_once()


class EventApiCsrfTest(TestCase):
    def test_event_post_allows_unauthenticated_access(self):
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            "/api/events/",
            data={
                "name": "CSRF Safe Event",
                "location": "Test Venue",
                "start_datetime": timezone.now().isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


@override_settings(
    CHECKIN_DOMAIN="https://frontend.example.com",
    RSVP_DOMAIN="https://frontend.example.com",
)
class CheckinLinkGenerationTest(TestCase):
    def test_rsvp_url_uses_frontend_domain_and_route(self):
        event = make_event()
        guest = make_guest(event, is_placeholder=True, email=None)

        url = build_rsvp_url(guest)

        self.assertEqual(url, f"https://frontend.example.com/rsvp/{guest.unique_token}/")

    def test_email_contains_qr_image_from_media_base_url(self):
        event = make_event()
        guest = make_guest(event)

        with override_settings(MEDIA_BASE_URL="https://api.example.com"):
            html_content = _build_html_content(guest)
        self.assertIn("https://api.example.com/media/", html_content)


@override_settings(CHECKIN_DOMAIN="https://frontend.example.com", MEDIA_ROOT=str(TEST_MEDIA_ROOT))
class EmailQrEmbeddingTest(TestCase):
    def test_email_html_contains_embedded_qr_and_attachment_message(self):
        os.makedirs(TEST_MEDIA_ROOT / "qr_codes", exist_ok=True)
        event = make_event()
        guest = make_guest(event)
        generate_qr_code(guest)
        guest.refresh_from_db()

        html_content = _build_html_content(guest)
        self.assertIn("Your QR code is shown above and also attached", html_content)
        self.assertIn("Guest QR code", html_content)
        self.assertNotIn("RSVP", html_content)
        self.assertNotIn("Check-in Link", html_content)

        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


@override_settings(MEDIA_ROOT=str(TEST_MEDIA_ROOT))
class EventLogoLoadingTest(TestCase):
    def test_load_event_logo_reads_from_storage_file_open(self):
        os.makedirs(TEST_MEDIA_ROOT / "event_logos", exist_ok=True)
        event = make_event()

        img = Image.new("RGBA", (20, 20), (255, 0, 0, 255))
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        event.logo.save("logo.png", ContentFile(buf.read()), save=True)

        loaded = _load_event_logo(event, 20)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.size, (20, 20))

        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
