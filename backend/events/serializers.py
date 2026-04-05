from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "location",
            "start_datetime",
            "end_datetime",
            "qr_color",
            "qr_caption",
            "logo",
            "is_active",
            "registration_type",
            "registration_fields",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
