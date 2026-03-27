from django.contrib import admin
from .models import CheckInLog


@admin.register(CheckInLog)
class CheckInLogAdmin(admin.ModelAdmin):
    list_display = ["guest", "scanned_at", "scanned_by"]
    list_filter = ["scanned_at"]
    readonly_fields = ["guest", "scanned_at", "scanned_by"]
