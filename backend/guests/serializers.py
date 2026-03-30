from rest_framework import serializers
from .models import Guest


class GuestSerializer(serializers.ModelSerializer):
    """Read-oriented serializer for a single guest."""

    qr_code_url = serializers.SerializerMethodField()
    rsvp_link = serializers.SerializerMethodField()

    class Meta:
        model = Guest
        fields = [
            "id",
            "event",
            "name",
            "email",
            "phone",
            "table_number",
            "qr_code_url",
            "rsvp_link",
            "has_checked_in",
            "check_in_time",
            "rsvp_status",
            "rsvp_time",
            "is_placeholder",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "qr_code_url",
            "rsvp_link",
            "has_checked_in",
            "check_in_time",
            "rsvp_time",
            "is_placeholder",
            "created_at",
        ]

    def get_qr_code_url(self, obj):
        request = self.context.get("request")
        if obj.qr_code_image and request:
            return request.build_absolute_uri(obj.qr_code_image.url)
        if obj.qr_code_image:
            return obj.qr_code_image.url
        return None

    def get_rsvp_link(self, obj):
        from core.services.rsvp_service import build_rsvp_url

        return build_rsvp_url(obj)


class BulkGuestCreateSerializer(serializers.Serializer):
    """Accepts a list of guest objects for bulk creation (email or phone)."""

    guests = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )

    def validate_guests(self, guests):
        required = {"name"}
        for i, guest in enumerate(guests):
            missing = required - set(guest.keys())
            if missing:
                raise serializers.ValidationError(
                    f"Guest at index {i} is missing fields: {missing}"
                )
        return guests


class RSVPSubmissionSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    rsvp_status = serializers.ChoiceField(choices=Guest.RSVP_STATUS_CHOICES)

