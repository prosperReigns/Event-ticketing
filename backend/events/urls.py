from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, PublicEventDetailView, PublicEventRegisterView

router = DefaultRouter()
router.register(r"events", EventViewSet, basename="event")

urlpatterns = [
    path("", include(router.urls)),
    # Legacy UUID-based registration endpoint (kept for backward compatibility)
    path("events/<uuid:pk>/register/", PublicEventRegisterView.as_view(), name="event-public-register"),
    # Slug-based public endpoints
    path("events/public/<slug:event_slug>/", PublicEventDetailView.as_view(), name="event-public-detail"),
    path("events/public/<slug:event_slug>/register/", PublicEventRegisterView.as_view(), name="event-public-register-slug"),
]
