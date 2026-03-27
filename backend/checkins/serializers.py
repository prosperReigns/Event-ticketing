from rest_framework import serializers


class CheckInResponseSerializer(serializers.Serializer):
    """Serializer for a successful check-in response."""

    guest_name = serializers.CharField()
    table_number = serializers.CharField()
    event_name = serializers.CharField()
    check_in_time = serializers.DateTimeField()
    message = serializers.CharField()
