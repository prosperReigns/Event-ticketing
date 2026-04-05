import logging

from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from guests.models import Guest, GuestResponse
from core.services.qr_service import generate_qr_code
from core.services.email_service import send_guest_qr_email
from .models import Event
from .serializers import EventSerializer

logger = logging.getLogger(__name__)

# Default registration fields used when an event has none configured.
_DEFAULT_REGISTRATION_FIELDS = [
    {"name": "full_name", "type": "text", "required": True, "label": "Full Name"},
    {"name": "email", "type": "email", "required": True, "label": "Email"},
    {"name": "phone", "type": "tel", "required": False, "label": "Phone Number"},
]


def _get_effective_fields(event):
    """Return the event's effective registration fields.

    Base fields (full_name, email, phone) are always included.  When the event has
    custom registration_fields they are used, with any missing base fields
    prepended so that name and email are always collected.
    """
    if not event.registration_fields:
        return _DEFAULT_REGISTRATION_FIELDS

    custom_names = {f["name"] for f in event.registration_fields}
    prepend = [f for f in _DEFAULT_REGISTRATION_FIELDS if f["name"] not in custom_names]
    return prepend + event.registration_fields


def _validate_registration_data(data, fields):
    """
    Validate *data* dict against *fields* spec.

    Returns (errors: dict, validated: dict).  *errors* is empty on success.
    Supported field types: text, email, number, select, radio, checkbox, textarea.
    """
    errors = {}
    validated = {}

    for field in fields:
        field_name = field["name"]
        field_type = field.get("type", "text")
        required = field.get("required", False)
        options = field.get("options", [])

        raw = data.get(field_name, "")

        # Checkbox fields expect a list of selected values.
        if field_type == "checkbox":
            if isinstance(raw, list):
                value = raw
            elif raw:
                value = [raw]
            else:
                value = []

            if required and not value:
                errors[field_name] = "This field is required."
                continue

            if value and options:
                invalid = [v for v in value if v not in options]
                if invalid:
                    errors[field_name] = (
                        f"Invalid choices: {', '.join(str(v) for v in invalid)}."
                    )
                    continue

            validated[field_name] = value
            continue

        value = raw.strip() if isinstance(raw, str) else raw

        has_value = value != "" and value is not None

        if required and not has_value:
            errors[field_name] = "This field is required."
            continue

        if has_value:
            if field_type == "email":
                try:
                    validate_email(str(value))
                except DjangoValidationError:
                    errors[field_name] = "Enter a valid email address."
                    continue

            if field_type == "number":
                try:
                    float(str(value))
                except (ValueError, TypeError):
                    errors[field_name] = "Enter a valid number."
                    continue

            if field_type in ("select", "radio") and options and value not in options:
                errors[field_name] = (
                    f"Invalid choice. Valid options are: {', '.join(options)}."
                )
                continue

        validated[field_name] = value

    return errors, validated


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for creating, listing and retrieving events.
    Event management is currently open because frontend auth is not yet enabled.
    """

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    # Public API endpoint; avoid session CSRF checks for cross-origin POSTs.
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_throttles(self):
        # Writes still use global throttle rates to reduce abuse.
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return []
        return super().get_throttles()


class PublicEventDetailView(APIView):
    """
    GET /api/events/slug/{slug}/  – retrieve a public event by its slug.

    Used by the frontend registration page to display event details before
    the user submits their information.  Returns 403 if the event is not
    open for public registration.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        try:
            event = Event.objects.get(slug=slug)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        if event.registration_type != Event.REGISTRATION_PUBLIC:
            return Response(
                {"detail": "This event is not open for public registration."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = EventSerializer(event)
        data = {**serializer.data, "registration_fields": _get_effective_fields(event)}
        return Response(data)


class PublicEventRegisterView(APIView):
    """
    POST /api/events/{pk}/register/  – self-register for a public event.
    POST /api/events/slug/{slug}/guests/  – self-register using event slug.

    Accepts name and email, creates a Guest, generates a QR code and sends
    the invitation email.  Returns 403 if the event is not public.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def _get_event(self, pk=None, slug=None):
        """Look up an event by UUID pk or slug."""
        try:
            if slug is not None:
                return Event.objects.get(slug=slug), None
            return Event.objects.get(pk=pk), None
        except Event.DoesNotExist:
            return None, Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk=None, slug=None):
        event, error = self._get_event(pk=pk, slug=slug)
        if error:
            return error

        if event.registration_type != Event.REGISTRATION_PUBLIC:
            return Response(
                {"detail": "This event is not open for public registration."},
                status=status.HTTP_403_FORBIDDEN,
            )

        fields = _get_effective_fields(event)
        errors, validated = _validate_registration_data(request.data, fields)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract canonical name/email/phone from the validated payload.
        # Support both 'full_name' (default key) and 'name' so that events
        # with a custom field named 'name' also work correctly.
        name = (validated.get("full_name") or validated.get("name", "")).strip()
        email = validated.get("email", "").strip().lower()
        phone = validated.get("phone", "").strip()

        # Safety net: if the event's custom registration_fields omit any name
        # field entirely, validated won't contain 'full_name'/'name' and we'd
        # create a Guest with an empty name string.  Catch that misconfiguration
        # early with a clear error rather than a silent DB-level issue.
        if not name:
            return Response({"full_name": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

        if Guest.objects.filter(event=event, email__iexact=email).exists():
            return Response(
                {"detail": "You have already registered for this event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        guest = Guest.objects.create(
            event=event,
            name=name,
            email=email,
            phone=phone,
            rsvp_status=Guest.RSVP_STATUS_ATTENDING,
            is_placeholder=False,
        )

        GuestResponse.objects.create(event=event, guest=guest, data=validated)

        try:
            generate_qr_code(guest)
        except (OSError, ValueError) as exc:
            logger.exception(
                "Public registration QR generation failed for guest %s: %s", guest.id, exc
            )

        send_guest_qr_email(guest)

        return Response(
            {"detail": "Registration successful. Your QR code has been sent to your email."},
            status=status.HTTP_201_CREATED,
        )
