from django.contrib import admin
from .models import Lead, LeadActivity, MessageQueue

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "mobile", "stage", "club", "updated_at")
    list_filter = ("club", "stage")
    search_fields = ("first_name", "last_name", "mobile")
    readonly_fields = ("created_at", "updated_at")

admin.site.register(LeadActivity)
admin.site.register(MessageQueue)
