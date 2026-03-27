from django.contrib import admin
from .models import Guest


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "event", "table_number", "has_checked_in", "check_in_time"]
    list_filter = ["has_checked_in", "event"]
    search_fields = ["name", "email"]
    readonly_fields = ["unique_token", "qr_code_image", "has_checked_in", "check_in_time", "created_at"]
