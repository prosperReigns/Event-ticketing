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
from guests.models import Guest, GuestResponse
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
        generate_qr_code(guest)
        guest.refresh_from_db()

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


# ---------------------------------------------------------------------------
# Public event registration tests
# ---------------------------------------------------------------------------

@override_settings(SEND_EMAIL_ASYNC=False, SECURE_SSL_REDIRECT=False)
@patch("events.views.generate_qr_code")
@patch("events.views.send_guest_qr_email")
class PublicEventRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.public_event = Event.objects.create(
            name="Public Gala",
            location="Main Hall",
            start_datetime=timezone.now() + timedelta(hours=2),
            registration_type=Event.REGISTRATION_PUBLIC,
        )
        self.private_event = Event.objects.create(
            name="Private Party",
            location="VIP Room",
            start_datetime=timezone.now() + timedelta(hours=2),
            registration_type=Event.REGISTRATION_PRIVATE,
        )
        self.url = f"/api/events/{self.public_event.id}/register/"
        self.private_url = f"/api/events/{self.private_event.id}/register/"

    def test_successful_registration(self, mock_email, mock_qr):
        response = self.client.post(
            self.url,
            {"full_name": "Jane Doe", "email": "jane@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Registration successful", response.data["detail"])
        self.assertTrue(Guest.objects.filter(event=self.public_event, email="jane@example.com").exists())
        mock_qr.assert_called_once()
        mock_email.assert_called_once()

    def test_registration_sets_attending_status(self, mock_email, mock_qr):
        self.client.post(
            self.url,
            {"full_name": "Jane Doe", "email": "jane@example.com"},
            format="json",
        )
        guest = Guest.objects.get(event=self.public_event, email="jane@example.com")
        self.assertEqual(guest.rsvp_status, Guest.RSVP_STATUS_ATTENDING)
        self.assertFalse(guest.is_placeholder)

    def test_private_event_returns_403(self, mock_email, mock_qr):
        response = self.client.post(
            self.private_url,
            {"full_name": "Jane Doe", "email": "jane@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_qr.assert_not_called()
        mock_email.assert_not_called()

    def test_missing_email_returns_400(self, mock_email, mock_qr):
        response = self.client.post(
            self.url,
            {"full_name": "Jane Doe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_name_returns_400(self, mock_email, mock_qr):
        response = self.client.post(
            self.url,
            {"email": "jane@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_registration_returns_400(self, mock_email, mock_qr):
        self.client.post(
            self.url,
            {"full_name": "Jane Doe", "email": "jane@example.com"},
            format="json",
        )
        response = self.client.post(
            self.url,
            {"full_name": "Jane Again", "email": "jane@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already registered", response.data["detail"])

    def test_nonexistent_event_returns_404(self, mock_email, mock_qr):
        response = self.client.post(
            f"/api/events/{uuid.uuid4()}/register/",
            {"full_name": "Jane Doe", "email": "jane@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(FRONTEND_URL="https://app.example.com", SECURE_SSL_REDIRECT=False)
class EventPublicLinkTest(TestCase):
    def test_get_public_link_returns_correct_url(self):
        event = make_event()
        link = event.get_public_link()
        self.assertEqual(link, f"https://app.example.com/register/{event.slug}")

    def test_event_detail_api_includes_registration_type(self):
        client = APIClient()
        event = Event.objects.create(
            name="Open Event",
            location="Arena",
            start_datetime=timezone.now(),
            registration_type=Event.REGISTRATION_PUBLIC,
        )
        response = client.get(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["registration_type"], Event.REGISTRATION_PUBLIC)

    def test_event_serializer_includes_slug(self):
        client = APIClient()
        event = Event.objects.create(
            name="Slug Test Event",
            location="Venue",
            start_datetime=timezone.now(),
        )
        response = client.get(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["slug"], "slug-test-event")

    def test_slug_auto_generated_from_name(self):
        event = Event.objects.create(
            name="My Awesome Event!",
            location="Venue",
            start_datetime=timezone.now(),
        )
        self.assertEqual(event.slug, "my-awesome-event")

    def test_duplicate_name_generates_unique_slug(self):
        event1 = Event.objects.create(
            name="Gala Night",
            location="Venue",
            start_datetime=timezone.now(),
        )
        event2 = Event.objects.create(
            name="Gala Night",
            location="Venue B",
            start_datetime=timezone.now(),
        )
        self.assertEqual(event1.slug, "gala-night")
        self.assertTrue(event2.slug.startswith("gala-night-"))
        self.assertNotEqual(event2.slug, event1.slug)


@patch("events.views.send_guest_qr_email")
@patch("events.views.generate_qr_code")
@override_settings(SECURE_SSL_REDIRECT=False)
class PublicEventBySlugTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.public_event = Event.objects.create(
            name="Public Gala Slug",
            location="Main Hall",
            start_datetime=timezone.now() + timedelta(hours=2),
            registration_type=Event.REGISTRATION_PUBLIC,
        )
        self.private_event = Event.objects.create(
            name="Private Party Slug",
            location="VIP Room",
            start_datetime=timezone.now() + timedelta(hours=2),
            registration_type=Event.REGISTRATION_PRIVATE,
        )

    def test_public_event_detail_by_slug(self, mock_qr, mock_email):
        response = self.client.get(f"/api/events/slug/{self.public_event.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.public_event.name)
        self.assertEqual(response.data["slug"], self.public_event.slug)

    def test_private_event_detail_by_slug_returns_403(self, mock_qr, mock_email):
        response = self.client.get(f"/api/events/slug/{self.private_event.slug}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_slug_returns_404(self, mock_qr, mock_email):
        response = self.client.get("/api/events/slug/no-such-event/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_successful_registration_by_slug(self, mock_qr, mock_email):
        response = self.client.post(
            f"/api/events/slug/{self.public_event.slug}/guests/",
            {"full_name": "Slug User", "email": "sluguser@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Registration successful", response.data["detail"])
        self.assertTrue(
            Guest.objects.filter(event=self.public_event, email="sluguser@example.com").exists()
        )
        mock_qr.assert_called_once()
        mock_email.assert_called_once()

    def test_private_event_register_by_slug_returns_403(self, mock_qr, mock_email):
        response = self.client.post(
            f"/api/events/slug/{self.private_event.slug}/guests/",
            {"full_name": "Slug User", "email": "sluguser@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_qr.assert_not_called()
        mock_email.assert_not_called()

    def test_nonexistent_event_register_by_slug_returns_404(self, mock_qr, mock_email):
        response = self.client.post(
            "/api/events/slug/no-such-event/guests/",
            {"full_name": "Slug User", "email": "sluguser@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Dynamic registration fields tests
# ---------------------------------------------------------------------------

@override_settings(SEND_EMAIL_ASYNC=False, SECURE_SSL_REDIRECT=False)
@patch("events.views.generate_qr_code")
@patch("events.views.send_guest_qr_email")
class DynamicRegistrationFieldsTest(TestCase):
    """Tests for event-specific dynamic registration form fields."""

    def setUp(self):
        self.client = APIClient()

    # ------------------------------------------------------------------
    # Default fields (event with empty registration_fields)
    # ------------------------------------------------------------------

    def test_default_fields_accept_full_name_and_email(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Default Fields Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Alice Smith", "email": "alice@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Guest.objects.filter(event=event, email="alice@example.com").exists())

    def test_default_fields_require_full_name(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Default Required Test",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"email": "alice@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("full_name", response.data)

    def test_default_fields_require_email(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Default Email Required",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Alice Smith"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_invalid_email_format_rejected(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Email Format Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Alice Smith", "email": "not-an-email"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    # ------------------------------------------------------------------
    # Custom fields on the event
    # ------------------------------------------------------------------

    def test_custom_required_field_validated(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Custom Field Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {"name": "company", "type": "text", "required": True, "label": "Company"},
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Bob Jones", "email": "bob@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company", response.data)

    def test_custom_required_field_accepted_when_present(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Custom Required Accepted",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {"name": "company", "type": "text", "required": True, "label": "Company"},
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Bob Jones", "email": "bob@example.com", "company": "Acme"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_optional_custom_field_not_required(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Optional Field Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {"name": "dietary", "type": "text", "required": False, "label": "Dietary needs"},
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Carol White", "email": "carol@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_select_field_rejects_invalid_option(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Select Field Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {
                    "name": "meal",
                    "type": "select",
                    "required": True,
                    "label": "Meal preference",
                    "options": ["Vegan", "Non-veg", "Halal"],
                },
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Dave Green", "email": "dave@example.com", "meal": "Keto"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("meal", response.data)

    def test_select_field_accepts_valid_option(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Select Valid Option",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {
                    "name": "meal",
                    "type": "select",
                    "required": True,
                    "label": "Meal preference",
                    "options": ["Vegan", "Non-veg", "Halal"],
                },
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Eve Brown", "email": "eve@example.com", "meal": "Vegan"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # GuestResponse saving
    # ------------------------------------------------------------------

    def test_guest_response_created_on_registration(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Response Saved Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {"name": "company", "type": "text", "required": False, "label": "Company"},
            ],
        )
        self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Frank Black", "email": "frank@example.com", "company": "Tech Co"},
            format="json",
        )
        guest = Guest.objects.get(event=event, email="frank@example.com")
        self.assertTrue(GuestResponse.objects.filter(event=event, guest=guest).exists())

    def test_guest_response_data_contains_submitted_fields(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Response Data Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {"name": "company", "type": "text", "required": False, "label": "Company"},
            ],
        )
        self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Grace Hall", "email": "grace@example.com", "company": "Startup"},
            format="json",
        )
        response = GuestResponse.objects.get(event=event)
        self.assertEqual(response.data["full_name"], "Grace Hall")
        self.assertEqual(response.data["email"], "grace@example.com")
        self.assertEqual(response.data["company"], "Startup")

    def test_guest_response_created_for_default_fields(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Default Response Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
        )
        self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Hank Fox", "email": "hank@example.com"},
            format="json",
        )
        self.assertEqual(GuestResponse.objects.filter(event=event).count(), 1)
        gr = GuestResponse.objects.get(event=event)
        self.assertEqual(gr.data["full_name"], "Hank Fox")
        self.assertEqual(gr.data["email"], "hank@example.com")

    # ------------------------------------------------------------------
    # registration_fields included in EventSerializer
    # ------------------------------------------------------------------

    def test_event_serializer_exposes_registration_fields(self, mock_email, mock_qr):
        fields = [
            {"name": "full_name", "type": "text", "required": True},
            {"name": "email", "type": "email", "required": True},
        ]
        event = Event.objects.create(
            name="Serializer Fields Event",
            location="Venue",
            start_datetime=timezone.now(),
            registration_fields=fields,
        )
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["registration_fields"], fields)

    def test_event_serializer_registration_fields_empty_by_default(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="No Fields Event",
            location="Venue",
            start_datetime=timezone.now(),
        )
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["registration_fields"], [])

    # ------------------------------------------------------------------
    # New field types: number, radio, checkbox
    # ------------------------------------------------------------------

    def test_number_field_accepts_valid_number(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Number Field Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {"name": "age", "type": "number", "required": True, "label": "Age"},
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Alice", "email": "alice@example.com", "age": "25"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_number_field_rejects_non_numeric(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Number Reject Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {"name": "age", "type": "number", "required": True, "label": "Age"},
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Bob", "email": "bob@example.com", "age": "not-a-number"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("age", response.data)

    def test_radio_field_accepts_valid_option(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Radio Field Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {
                    "name": "tshirt",
                    "type": "radio",
                    "required": True,
                    "label": "T-shirt size",
                    "options": ["S", "M", "L", "XL"],
                },
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Carol", "email": "carol@example.com", "tshirt": "M"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_radio_field_rejects_invalid_option(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Radio Reject Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {
                    "name": "tshirt",
                    "type": "radio",
                    "required": True,
                    "label": "T-shirt size",
                    "options": ["S", "M", "L", "XL"],
                },
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Dave", "email": "dave@example.com", "tshirt": "XXL"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tshirt", response.data)

    def test_checkbox_field_accepts_valid_options_list(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Checkbox Field Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {
                    "name": "interests",
                    "type": "checkbox",
                    "required": False,
                    "label": "Interests",
                    "options": ["Music", "Art", "Tech", "Sports"],
                },
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Eve", "email": "eve@example.com", "interests": ["Music", "Tech"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        gr = GuestResponse.objects.get(event=event)
        self.assertEqual(gr.data["interests"], ["Music", "Tech"])

    def test_checkbox_required_field_rejects_empty(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Checkbox Required Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {
                    "name": "interests",
                    "type": "checkbox",
                    "required": True,
                    "label": "Interests",
                    "options": ["Music", "Art", "Tech"],
                },
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Frank", "email": "frank@example.com", "interests": []},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("interests", response.data)

    def test_checkbox_rejects_invalid_option(self, mock_email, mock_qr):
        event = Event.objects.create(
            name="Checkbox Invalid Option Event",
            location="Venue",
            start_datetime=timezone.now() + timedelta(hours=1),
            registration_type=Event.REGISTRATION_PUBLIC,
            registration_fields=[
                {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
                {"name": "email", "type": "email", "required": True, "label": "Email"},
                {
                    "name": "interests",
                    "type": "checkbox",
                    "required": False,
                    "label": "Interests",
                    "options": ["Music", "Art", "Tech"],
                },
            ],
        )
        response = self.client.post(
            f"/api/events/{event.id}/register/",
            {"full_name": "Grace", "email": "grace@example.com", "interests": ["Music", "Cooking"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("interests", response.data)
