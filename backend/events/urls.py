from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, PublicEventDetailView, PublicEventRegisterView

router = DefaultRouter()
router.register(r"events", EventViewSet, basename="event")

urlpatterns = [
    path("", include(router.urls)),
    path("events/<uuid:pk>/register/", PublicEventRegisterView.as_view(), name="event-public-register"),
    path("events/slug/<slug:slug>/", PublicEventDetailView.as_view(), name="event-detail-by-slug"),
    path("events/slug/<slug:slug>/guests/", PublicEventRegisterView.as_view(), name="event-guest-register-by-slug"),
]
