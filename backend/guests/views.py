from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from events.models import Event
from .models import Guest
from .serializers import BulkGuestCreateSerializer, GuestSerializer
from core.services.guest_service import bulk_create_guests


class GuestListCreateView(APIView):
    """
    GET  /api/events/{event_id}/guests/  – list guests for an event
    POST /api/events/{event_id}/guests/  – bulk-create guests
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

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

        http_status = status.HTTP_201_CREATED
        if created and errors:
            http_status = status.HTTP_207_MULTI_STATUS
        elif not created:
            http_status = status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=http_status)
