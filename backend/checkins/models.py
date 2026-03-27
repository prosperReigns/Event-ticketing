from django.db import models
from django.contrib.auth import get_user_model
from guests.models import Guest

User = get_user_model()


class CheckInLog(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="checkin_logs")
    scanned_at = models.DateTimeField(auto_now_add=True)
    scanned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkin_logs",
    )

    class Meta:
        ordering = ["-scanned_at"]

    def __str__(self):
        return f"CheckIn: {self.guest.name} at {self.scanned_at}"
