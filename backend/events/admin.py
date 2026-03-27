from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "start_datetime", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "location"]
