import logging

from rest_framework import viewsets, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from guests.models import Guest
from core.services.qr_service import generate_qr_code
from core.services.email_service import send_guest_qr_email
from .models import Event
from .serializers import EventSerializer

logger = logging.getLogger(__name__)


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


class PublicEventRegisterView(APIView):
    """
    POST /api/events/{pk}/register/  – self-register for a public event.

    Accepts name and email, creates a Guest, generates a QR code and sends
    the invitation email.  Returns 403 if the event is not public.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        if event.registration_type != Event.REGISTRATION_PUBLIC:
            return Response(
                {"detail": "This event is not open for public registration."},
                status=status.HTTP_403_FORBIDDEN,
            )

        name = str(request.data.get("name", "")).strip()
        email = str(request.data.get("email", "")).strip().lower()

        if not name:
            return Response(
                {"detail": "Name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Guest.objects.filter(event=event, email__iexact=email).exists():
            return Response(
                {"detail": "You have already registered for this event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        guest = Guest.objects.create(
            event=event,
            name=name,
            email=email,
            rsvp_status=Guest.RSVP_STATUS_ATTENDING,
            is_placeholder=False,
        )

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
