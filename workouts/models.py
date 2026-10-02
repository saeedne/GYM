from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Exercise(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="exercises", verbose_name="باشگاه")
    name = models.CharField("نام حرکت", max_length=140)
    muscle_group = models.CharField("گروه عضلانی", max_length=100, blank=True)
    equipment = models.CharField("وسیله", max_length=100, blank=True)
    instructions = models.TextField("نحوه اجرا", blank=True)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["muscle_group", "name"]
        constraints = [models.UniqueConstraint(fields=["club", "name"], name="uniq_exercise_name_per_club")]
        verbose_name = "حرکت تمرینی"
        verbose_name_plural = "بانک حرکات"

    def __str__(self):
        return self.name


class WorkoutPlan(models.Model):
    LEVELS = [("beginner", "مبتدی"), ("intermediate", "متوسط"), ("advanced", "پیشرفته")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="workout_plans", verbose_name="باشگاه")
    name = models.CharField("نام برنامه", max_length=140)
    level = models.CharField("سطح", max_length=20, choices=LEVELS, default="beginner")
    trainer = models.ForeignKey("trainers.Trainer", on_delete=models.SET_NULL, null=True, blank=True, related_name="workout_plans", verbose_name="مربی")
    description = models.TextField("توضیحات", blank=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "برنامه تمرینی"
        verbose_name_plural = "برنامه‌های تمرینی"

    def clean(self):
        if self.trainer_id and self.trainer.club_id != self.club_id:
            raise ValidationError({"trainer": "مربی متعلق به باشگاه دیگری است."})

    def __str__(self):
        return self.name


class PlanExercise(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name="items", verbose_name="برنامه")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="plan_items", verbose_name="حرکت")
    day_number = models.PositiveSmallIntegerField("روز برنامه", default=1)
    sets = models.PositiveSmallIntegerField("ست", default=3)
    repetitions = models.CharField("تکرار/مدت", max_length=40, default="10")
    rest_seconds = models.PositiveSmallIntegerField("استراحت (ثانیه)", default=60)
    sort_order = models.PositiveSmallIntegerField("ترتیب", default=0)
    notes = models.CharField("یادداشت", max_length=160, blank=True)

    class Meta:
        ordering = ["day_number", "sort_order", "id"]
        constraints = [models.UniqueConstraint(fields=["plan", "day_number", "exercise"], name="uniq_exercise_per_plan_day")]
        verbose_name = "حرکت در برنامه"
        verbose_name_plural = "حرکات برنامه"

    def clean(self):
        if self.exercise_id and self.plan_id and self.exercise.club_id != self.plan.club_id:
            raise ValidationError({"exercise": "حرکت متعلق به باشگاه دیگری است."})


class WorkoutAssignment(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="workout_assignments")
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="workout_assignments", verbose_name="عضو")
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.PROTECT, related_name="assignments", verbose_name="برنامه")
    start_date = models.DateField("شروع برنامه")
    end_date = models.DateField("پایان برنامه", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    assigned_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField("یادداشت", blank=True)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "-id"]
        indexes = [models.Index(fields=["club", "member", "is_active"])]
        verbose_name = "انتساب برنامه"
        verbose_name_plural = "برنامه‌های اعضا"

    def clean(self):
        errors = {}
        if self.member_id and self.member.club_id != self.club_id:
            errors["member"] = "عضو متعلق به باشگاه دیگری است."
        if self.plan_id and self.plan.club_id != self.club_id:
            errors["plan"] = "برنامه متعلق به باشگاه دیگری است."
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "پایان برنامه قبل از شروع آن است."
        if errors:
            raise ValidationError(errors)


class BodyAssessment(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="body_assessments")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="body_assessments")
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="body_assessments", verbose_name="عضو")
    measured_on = models.DateField("تاریخ ارزیابی", default=timezone.localdate)
    height_cm = models.DecimalField("قد (سانتی‌متر)", max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField("وزن (کیلوگرم)", max_digits=5, decimal_places=1, null=True, blank=True)
    body_fat_percent = models.DecimalField("درصد چربی", max_digits=5, decimal_places=2, null=True, blank=True)
    waist_cm = models.DecimalField("دور کمر (سانتی‌متر)", max_digits=5, decimal_places=1, null=True, blank=True)
    chest_cm = models.DecimalField("دور سینه (سانتی‌متر)", max_digits=5, decimal_places=1, null=True, blank=True)
    notes = models.TextField("یادداشت", blank=True)
    assessed_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["-measured_on", "-id"]
        indexes = [models.Index(fields=["club", "member", "measured_on"])]
        verbose_name = "ارزیابی بدنی"
        verbose_name_plural = "ارزیابی‌های بدنی"

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (height_m * height_m), 1)
        return None

    def clean(self):
        if self.member_id and self.member.club_id != self.club_id:
            raise ValidationError({"member": "عضو متعلق به باشگاه دیگری است."})
        if self.branch_id and self.branch.club_id != self.club_id:
            raise ValidationError({"branch": "شعبه متعلق به باشگاه دیگری است."})
