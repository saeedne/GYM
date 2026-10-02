from django.contrib import admin
from .models import ClassBooking, FitnessClass, Trainer


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("display_name", "club", "branch", "mobile", "specialty", "is_active")
    list_filter = ("club", "branch", "is_active")
    search_fields = ("display_name", "mobile", "specialty")


class ClassBookingInline(admin.TabularInline):
    model = ClassBooking
    extra = 0


@admin.register(FitnessClass)
class FitnessClassAdmin(admin.ModelAdmin):
    list_display = ("title", "club", "branch", "trainer", "starts_at", "capacity", "status")
    list_filter = ("club", "branch", "status")
    search_fields = ("title", "trainer__display_name")
    inlines = [ClassBookingInline]


@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ("fitness_class", "member", "club", "status", "booked_at")
    list_filter = ("club", "status")
    search_fields = ("member__member_code", "member__first_name", "member__last_name", "fitness_class__title")
