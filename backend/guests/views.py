import logging

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from django.utils import timezone

from events.models import Event
from .models import Guest
from .serializers import (
    BulkGuestCreateSerializer,
    GuestSerializer,
    RSVPSubmissionSerializer,
)
from core.services.guest_service import bulk_create_guests
from core.services.qr_service import generate_qr_code
from core.services.email_service import send_guest_qr_email

logger = logging.getLogger(__name__)

class GuestListCreateView(APIView):
    """
    GET  /api/events/{event_id}/guests/  – list guests for an event
    POST /api/events/{event_id}/guests/  – bulk-create guests
    """

    permission_classes = [permissions.AllowAny]

    def _get_event(self, event_id):
        try:
            return Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return None

    def get(self, request, event_id):
        event = self._get_event(event_id)
        if not event:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        guests = Guest.objects.filter(event=event).select_related("event")
        serializer = GuestSerializer(guests, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, event_id):
        event = self._get_event(event_id)
        if not event:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BulkGuestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        created, errors = bulk_create_guests(event, serializer.validated_data["guests"])

        response_data = {
            "created": GuestSerializer(created, many=True, context={"request": request}).data,
        }
        if errors:
            response_data["errors"] = errors
            if len(errors) == 1:
                response_data["detail"] = errors[0].get("error", "Guest creation failed.")
            else:
                response_data["detail"] = "Some guests could not be created."

        http_status = status.HTTP_201_CREATED
        if created and errors:
            http_status = status.HTTP_207_MULTI_STATUS
        elif not created:
            http_status = status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=http_status)


class RSVPView(APIView):
    """
    GET  /api/rsvp/{token}/  – fetch RSVP info for a guest
    POST /api/rsvp/{token}/  – submit RSVP response
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def _get_guest(self, token):
        try:
            return Guest.objects.select_related("event").get(unique_token=token)
        except Guest.DoesNotExist:
            return None

    def get(self, request, token):
        guest = self._get_guest(token)
        if not guest:
            return Response({"detail": "Guest not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = GuestSerializer(guest, context={"request": request})
        return Response(serializer.data)

    def post(self, request, token):
        guest = self._get_guest(token)
        if not guest:
            return Response({"detail": "Guest not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RSVPSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        rsvp_status = data["rsvp_status"]
        name = data.get("name") or guest.name
        phone = data.get("phone", guest.phone) or ""
        email = data.get("email", guest.email)

        if rsvp_status == Guest.RSVP_STATUS_ATTENDING and not email:
            return Response(
                {"detail": "Email is required to confirm attendance."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        normalized_email = email.strip().lower() if email else None
        if normalized_email:
            duplicate = (
                Guest.objects.filter(event=guest.event, email__iexact=normalized_email)
                .exclude(id=guest.id)
                .exists()
            )
            if duplicate:
                return Response(
                    {"detail": "Guest with this email already exists for the event."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        guest.name = name
        guest.phone = phone
        guest.email = normalized_email
        guest.rsvp_status = rsvp_status
        guest.rsvp_time = timezone.now()
        if normalized_email:
            guest.is_placeholder = False
        guest.save(
            update_fields=["name", "phone", "email", "rsvp_status", "rsvp_time", "is_placeholder"]
        )

        if guest.rsvp_status == Guest.RSVP_STATUS_ATTENDING:
            if not guest.qr_code_image:
                try:
                    generate_qr_code(guest)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "RSVP QR generation failed for guest %s: %s", guest.id, exc
                    )
            send_guest_qr_email(guest)

        response = GuestSerializer(guest, context={"request": request})
        return Response(response.data, status=status.HTTP_200_OK)
