import uuid
from django.db import models


class Event(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_datetime"]

    def __str__(self):
        return f"{self.name} ({self.start_datetime})"
