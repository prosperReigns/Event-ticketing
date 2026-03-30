from rest_framework import viewsets, permissions
from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for creating, listing and retrieving events.
    Event management is currently open because frontend auth is not yet enabled.
    """

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        return [permissions.AllowAny()]
