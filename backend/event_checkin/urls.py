"""
URL configuration for event_checkin project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("events.urls")),
    path("api/", include("guests.urls")),
    path("api/", include("checkins.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
