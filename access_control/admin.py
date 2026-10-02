from django.contrib import admin
from .models import AccessCredential, AccessPolicy, GuestPass


@admin.register(AccessPolicy)
class AccessPolicyAdmin(admin.ModelAdmin):
    list_display = ("club", "enforce_hours", "enforce_days")


@admin.register(AccessCredential)
class AccessCredentialAdmin(admin.ModelAdmin):
    list_display = ("member", "club", "credential_type", "token", "is_active", "last_used_at")
    list_filter = ("club", "credential_type", "is_active")
    search_fields = ("token", "member__member_code", "member__first_name", "member__last_name")


@admin.register(GuestPass)
class GuestPassAdmin(admin.ModelAdmin):
    list_display = ("pass_code", "guest_name", "club", "host_member", "valid_on", "status")
    list_filter = ("club", "status", "valid_on")
    search_fields = ("pass_code", "guest_name", "guest_mobile")
