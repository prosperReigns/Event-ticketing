from django.contrib import admin
from .models import Guest


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "event",
        "table_number",
        "rsvp_status",
        "is_placeholder",
        "has_checked_in",
        "check_in_time",
    ]
    list_filter = ["has_checked_in", "rsvp_status", "is_placeholder", "event"]
    search_fields = ["name", "email"]
    readonly_fields = [
        "unique_token",
        "qr_code_image",
        "has_checked_in",
        "check_in_time",
        "rsvp_time",
        "created_at",
    ]
