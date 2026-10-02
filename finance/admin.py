from django.contrib import admin
from .models import CashAccount, FinanceCategory, FinanceEntry


@admin.register(CashAccount)
class CashAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "branch", "opening_balance", "is_active")
    list_filter = ("club", "branch", "is_active")


@admin.register(FinanceCategory)
class FinanceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "entry_type", "is_active")
    list_filter = ("club", "entry_type", "is_active")


@admin.register(FinanceEntry)
class FinanceEntryAdmin(admin.ModelAdmin):
    list_display = ("occurred_on", "club", "entry_type", "amount", "category", "source", "description")
    list_filter = ("club", "entry_type", "source", "occurred_on")
    search_fields = ("description", "source_id")
    readonly_fields = ("created_at",)
