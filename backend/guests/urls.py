from django.urls import path
from .views import GuestListCreateView

urlpatterns = [
    path(
        "events/<uuid:event_id>/guests/",
        GuestListCreateView.as_view(),
        name="guest-list-create",
    ),
]
