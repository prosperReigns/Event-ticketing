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
    # Public API endpoint until auth is enabled; avoid session CSRF checks for cross-origin POSTs.
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_throttles(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return []
        return super().get_throttles()
