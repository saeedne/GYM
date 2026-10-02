from django.contrib import admin
from .models import BodyAssessment, Exercise, PlanExercise, WorkoutAssignment, WorkoutPlan


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "muscle_group", "equipment", "is_active")
    list_filter = ("club", "muscle_group", "is_active")
    search_fields = ("name", "muscle_group")


class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 1


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "level", "trainer", "is_active")
    list_filter = ("club", "level", "is_active")
    inlines = [PlanExerciseInline]


@admin.register(WorkoutAssignment)
class WorkoutAssignmentAdmin(admin.ModelAdmin):
    list_display = ("member", "plan", "club", "start_date", "end_date", "is_active")
    list_filter = ("club", "is_active")
    search_fields = ("member__member_code", "member__first_name", "plan__name")


@admin.register(BodyAssessment)
class BodyAssessmentAdmin(admin.ModelAdmin):
    list_display = ("member", "club", "measured_on", "height_cm", "weight_kg", "body_fat_percent")
    list_filter = ("club", "measured_on")
    search_fields = ("member__member_code", "member__first_name", "member__last_name")
