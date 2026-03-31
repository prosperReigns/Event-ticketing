from django.urls import path
from .views import GuestListCreateView, GuestDetailView, RSVPView

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
    path(
        "events/<uuid:event_id>/guests/<uuid:guest_id>/",
        GuestDetailView.as_view(),
        name="guest-detail",
    ),
]
