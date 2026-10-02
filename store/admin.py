from django.contrib import admin
from .models import InventoryMovement, Product, StoreSale


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "club", "branch", "stock_quantity", "sale_price", "is_active")
    list_filter = ("club", "branch", "category", "is_active")
    search_fields = ("sku", "name", "category")


@admin.register(StoreSale)
class StoreSaleAdmin(admin.ModelAdmin):
    list_display = ("product", "club", "branch", "member", "quantity", "unit_price", "sold_at")
    list_filter = ("club", "branch", "sold_at")


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "club", "movement_type", "quantity", "reason", "created_at")
    list_filter = ("club", "movement_type", "created_at")
