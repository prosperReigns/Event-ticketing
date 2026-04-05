from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "description",
            "location",
            "start_datetime",
            "end_datetime",
            "qr_color",
            "qr_caption",
            "logo",
            "is_active",
            "registration_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
