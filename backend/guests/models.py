import uuid
from django.db import models
from django.db.models import Q
from events.models import Event


class Guest(models.Model):
    RSVP_STATUS_PENDING = "pending"
    RSVP_STATUS_ATTENDING = "attending"
    RSVP_STATUS_DECLINED = "declined"
    RSVP_STATUS_CHOICES = [
        (RSVP_STATUS_PENDING, "Pending"),
        (RSVP_STATUS_ATTENDING, "Attending"),
        (RSVP_STATUS_DECLINED, "Declined"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="guests")
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, default="")
    table_number = models.CharField(max_length=50)
    unique_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    qr_code_image = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    has_checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    rsvp_status = models.CharField(
        max_length=20, choices=RSVP_STATUS_CHOICES, default=RSVP_STATUS_PENDING
    )
    rsvp_time = models.DateTimeField(null=True, blank=True)
    is_placeholder = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "email"],
                name="unique_event_email",
                condition=Q(email__isnull=False) & ~Q(email=""),
            )
        ]

    def __str__(self):
        return f"{self.name} – {self.event.name}"
