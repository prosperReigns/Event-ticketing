from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, PublicEventRegisterView

router = DefaultRouter()
router.register(r"events", EventViewSet, basename="event")

urlpatterns = [
    path("", include(router.urls)),
    path("events/<uuid:pk>/register/", PublicEventRegisterView.as_view(), name="event-public-register"),
]
