from django.contrib import admin
from .models import AuditLog, Branch, Club, ClubModule, SystemModule


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "status", "created_at")
    search_fields = ("name", "code", "slug")
    list_filter = ("status",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "code", "is_active")
    search_fields = ("name", "code", "club__name")
    list_filter = ("is_active", "club")


@admin.register(SystemModule)
class SystemModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "implemented", "sort_order")
    list_filter = ("implemented",)
    ordering = ("sort_order",)


@admin.register(ClubModule)
class ClubModuleAdmin(admin.ModelAdmin):
    list_display = ("club", "module", "enabled")
    list_filter = ("club", "enabled", "module")
    search_fields = ("club__name", "module__name", "module__code")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "club", "user", "action", "model_name", "object_id")
    list_filter = ("action", "club")
    search_fields = ("description", "object_id", "model_name")
    readonly_fields = ("created_at",)
