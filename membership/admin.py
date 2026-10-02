from django.contrib import admin
from .models import MembershipContract, MembershipPlan, Payment


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "code", "duration_days", "price", "is_active")
    list_filter = ("club", "is_active")
    search_fields = ("name", "code")


@admin.register(MembershipContract)
class MembershipContractAdmin(admin.ModelAdmin):
    list_display = ("contract_code", "club", "member", "plan", "start_date", "end_date", "status")
    list_filter = ("club", "status", "plan")
    search_fields = ("contract_code", "member__first_name", "member__last_name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("member", "club", "amount", "paid_on", "method", "status")
    list_filter = ("club", "status", "method", "paid_on")
    search_fields = ("reference", "member__first_name", "member__last_name")
