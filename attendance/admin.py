from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("member", "club", "branch", "check_in", "check_out", "status")
    list_filter = ("club", "branch", "status", "check_in")
    search_fields = ("member__member_code", "member__first_name", "member__last_name", "denial_reason")
    readonly_fields = ("created_at",)
