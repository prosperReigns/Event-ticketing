from rest_framework import viewsets, permissions
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for creating, listing and retrieving events.
    Event management is currently open because frontend auth is not yet enabled.
    """

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_throttles(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return []
        return super().get_throttles()

    def get_permissions(self):
        return [permissions.AllowAny()]
