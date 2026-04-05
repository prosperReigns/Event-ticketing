import uuid
from django.conf import settings
from django.db import models


class Event(models.Model):
    REGISTRATION_PRIVATE = "private"
    REGISTRATION_PUBLIC = "public"
    REGISTRATION_TYPE_CHOICES = [
        (REGISTRATION_PRIVATE, "Private"),
        (REGISTRATION_PUBLIC, "Public"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    location = models.CharField(max_length=500)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    qr_color = models.CharField(max_length=7, blank=True, default="#0f172a")
    qr_caption = models.CharField(max_length=120, blank=True, default="Scan to check in")
    logo = models.ImageField(upload_to="event_logos/", blank=True, null=True)
    is_active = models.BooleanField(default=False)
    registration_type = models.CharField(
        max_length=10,
        choices=REGISTRATION_TYPE_CHOICES,
        default=REGISTRATION_PRIVATE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_datetime"]

    def __str__(self):
        return f"{self.name} ({self.start_datetime})"

    def get_public_link(self):
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
        return f"{frontend_url}/register/{self.id}"
