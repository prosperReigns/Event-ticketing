import uuid
from django.db import models
from events.models import Event


class Guest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="guests")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, default="")
    table_number = models.CharField(max_length=50)
    unique_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    qr_code_image = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    has_checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("event", "email")]

    def __str__(self):
        return f"{self.name} – {self.event.name}"
