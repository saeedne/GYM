from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import ClubMembership, ClubRole, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("اطلاعات سیستم باشگاه", {"fields": ("display_name",)}),
    )
    list_display = ("username", "display_name", "is_staff", "is_active")


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "club", "branch", "role", "is_manager", "is_active")
    list_filter = ("club", "is_manager", "is_active")
    search_fields = ("user__username", "user__display_name", "club__name")


@admin.register(ClubRole)
class ClubRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "is_active", "created_at")
    list_filter = ("club", "is_active")
    search_fields = ("name", "club__name")
    filter_horizontal = ("permissions",)
