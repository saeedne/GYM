from django.contrib import admin
from .models import CafeOrder, MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "category", "price", "is_available")
    list_filter = ("club", "category", "is_available")
    search_fields = ("name", "category")


@admin.register(CafeOrder)
class CafeOrderAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "club", "branch", "member", "quantity", "status", "ordered_at")
    list_filter = ("club", "branch", "status", "ordered_at")
