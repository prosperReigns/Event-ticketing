from rest_framework import viewsets, permissions
from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for creating, listing and retrieving events.
    Write operations require authentication; reads are open.
    """

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
