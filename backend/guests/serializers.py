from rest_framework import serializers
from .models import Guest


class GuestSerializer(serializers.ModelSerializer):
    """Read-oriented serializer for a single guest."""

    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Guest
        fields = [
            "id",
            "event",
            "name",
            "email",
            "phone",
            "table_number",
            "unique_token",
            "qr_code_url",
            "has_checked_in",
            "check_in_time",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "unique_token",
            "qr_code_url",
            "has_checked_in",
            "check_in_time",
            "created_at",
        ]

    def get_qr_code_url(self, obj):
        request = self.context.get("request")
        if obj.qr_code_image and request:
            return request.build_absolute_uri(obj.qr_code_image.url)
        if obj.qr_code_image:
            return obj.qr_code_image.url
        return None


class BulkGuestCreateSerializer(serializers.Serializer):
    """Accepts a list of guest objects for bulk creation."""

    guests = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )

    def validate_guests(self, guests):
        required = {"name", "email", "table_number"}
        for i, guest in enumerate(guests):
            missing = required - set(guest.keys())
            if missing:
                raise serializers.ValidationError(
                    f"Guest at index {i} is missing fields: {missing}"
                )
        return guests
