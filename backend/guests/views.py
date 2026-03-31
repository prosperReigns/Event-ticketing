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

    def get_throttles(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return []
        return super().get_throttles()

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


class GuestDetailView(APIView):
    """
    DELETE /api/events/{event_id}/guests/{guest_id}/ â€“ remove a guest
    GET    /api/events/{event_id}/guests/{guest_id}/ â€“ fetch guest
    PATCH  /api/events/{event_id}/guests/{guest_id}/ â€“ update guest
    """

    permission_classes = [permissions.AllowAny]

    def get_throttles(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return []
        return super().get_throttles()

    def delete(self, request, event_id, guest_id):
        try:
            guest = Guest.objects.select_related("event").get(
                id=guest_id, event_id=event_id
            )
        except Guest.DoesNotExist:
            return Response({"detail": "Guest not found."}, status=status.HTTP_404_NOT_FOUND)

        guest.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, event_id, guest_id):
        try:
            guest = Guest.objects.select_related("event").get(
                id=guest_id, event_id=event_id
            )
        except Guest.DoesNotExist:
            return Response({"detail": "Guest not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = GuestSerializer(guest, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, event_id, guest_id):
        try:
            guest = Guest.objects.select_related("event").get(
                id=guest_id, event_id=event_id
            )
        except Guest.DoesNotExist:
            return Response({"detail": "Guest not found."}, status=status.HTTP_404_NOT_FOUND)

        name = str(request.data.get("name", guest.name)).strip()
        email = request.data.get("email", guest.email)
        phone = str(request.data.get("phone", guest.phone) or "").strip()
        table_number = str(request.data.get("table_number", guest.table_number) or "").strip()

        if not name:
            return Response(
                {"detail": "Guest name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        normalized_email = email.strip().lower() if isinstance(email, str) else email
        if normalized_email == "":
            normalized_email = None

        if not normalized_email and not phone:
            return Response(
                {"detail": "Each guest must include an email or phone number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(phone) > 30:
            return Response(
                {"detail": "Phone number cannot exceed 30 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if normalized_email:
            duplicate = (
                Guest.objects.filter(event_id=event_id, email__iexact=normalized_email)
                .exclude(id=guest.id)
                .exists()
            )
            if duplicate:
                return Response(
                    {"detail": "Guest with this email already exists for the event."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        guest.name = name
        guest.email = normalized_email
        guest.phone = phone
        guest.table_number = table_number
        guest.is_placeholder = not bool(normalized_email)
        guest.save(
            update_fields=["name", "email", "phone", "table_number", "is_placeholder"]
        )

        serializer = GuestSerializer(guest, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class RSVPView(APIView):
    """
    GET  /api/rsvp/{token}/  – fetch RSVP info for a guest
    POST /api/rsvp/{token}/  – submit RSVP response
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def _get_guest(self, token):
        """Return guest by RSVP token with related event, or None if missing."""
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
                except (OSError, ValueError) as exc:
                    logger.exception(
                        "RSVP QR generation failed for guest %s: %s", guest.id, exc
                    )
            send_guest_qr_email(guest)

        response = GuestSerializer(guest, context={"request": request})
        return Response(response.data, status=status.HTTP_200_OK)
