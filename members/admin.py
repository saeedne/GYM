from django.contrib import admin
from .models import Member

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("member_code", "first_name", "last_name", "club", "branch", "mobile", "status")
    list_filter = ("club", "branch", "status", "gender")
    search_fields = ("member_code", "first_name", "last_name", "mobile", "national_id")
