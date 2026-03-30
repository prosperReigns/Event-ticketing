from django.urls import path
from .views import GuestListCreateView, RSVPView

urlpatterns = [
    path(
        "events/<uuid:event_id>/guests/",
        GuestListCreateView.as_view(),
        name="guest-list-create",
    ),
    path(
        "rsvp/<uuid:token>/",
        RSVPView.as_view(),
        name="guest-rsvp",
    ),
]
