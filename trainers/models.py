from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Trainer(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="trainers", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="trainers", verbose_name="شعبه")
    display_name = models.CharField("نام مربی", max_length=120)
    mobile = models.CharField("موبایل", max_length=20, blank=True)
    specialty = models.CharField("تخصص", max_length=160, blank=True)
    bio = models.TextField("معرفی", blank=True)
    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="trainer_profiles", verbose_name="کاربر سامانه")
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["display_name"]
        constraints = [models.UniqueConstraint(fields=["club", "mobile"], condition=~Q(mobile=""), name="uniq_trainer_mobile_per_club")]
        verbose_name = "مربی"
        verbose_name_plural = "مربیان"

    def clean(self):
        if self.branch_id and self.branch.club_id != self.club_id:
            raise ValidationError({"branch": "شعبه باید متعلق به همین باشگاه باشد."})

    def __str__(self):
        return self.display_name


class FitnessClass(models.Model):
    STATUS = [("scheduled", "برنامه‌ریزی‌شده"), ("cancelled", "لغوشده"), ("completed", "برگزارشده")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="fitness_classes", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.PROTECT, related_name="fitness_classes", verbose_name="شعبه")
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, related_name="classes", verbose_name="مربی")
    title = models.CharField("نام کلاس", max_length=120)
    starts_at = models.DateTimeField("شروع")
    ends_at = models.DateTimeField("پایان")
    capacity = models.PositiveSmallIntegerField("ظرفیت", default=15)
    room = models.CharField("سالن", max_length=80, blank=True)
    description = models.TextField("توضیحات", blank=True)
    status = models.CharField("وضعیت", max_length=12, choices=STATUS, default="scheduled")
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [models.Index(fields=["club", "starts_at"])]
        verbose_name = "سانس کلاس"
        verbose_name_plural = "سانس‌های کلاس"

    def clean(self):
        errors = {}
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            errors["ends_at"] = "پایان کلاس باید بعد از زمان شروع باشد."
        if self.branch_id and self.branch.club_id != self.club_id:
            errors["branch"] = "شعبه متعلق به باشگاه دیگری است."
        if self.trainer_id and self.trainer.club_id != self.club_id:
            errors["trainer"] = "مربی متعلق به باشگاه دیگری است."
        if errors:
            raise ValidationError(errors)

    @property
    def booked_count(self):
        return self.bookings.filter(status="booked").count()

    @property
    def available_seats(self):
        return max(0, self.capacity - self.booked_count)

    def __str__(self):
        return f"{self.title} — {self.starts_at:%Y-%m-%d %H:%M}"


class ClassBooking(models.Model):
    STATUS = [("booked", "رزرو قطعی"), ("waitlist", "فهرست انتظار"), ("cancelled", "لغوشده"), ("attended", "حاضر")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="class_bookings", verbose_name="باشگاه")
    fitness_class = models.ForeignKey(FitnessClass, on_delete=models.CASCADE, related_name="bookings", verbose_name="کلاس")
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="class_bookings", verbose_name="عضو")
    status = models.CharField("وضعیت رزرو", max_length=12, choices=STATUS, default="booked")
    booked_at = models.DateTimeField("زمان رزرو", auto_now_add=True)
    attended_at = models.DateTimeField("زمان حضور", null=True, blank=True)

    class Meta:
        ordering = ["booked_at"]
        constraints = [models.UniqueConstraint(fields=["fitness_class", "member"], name="uniq_member_per_class")]
        verbose_name = "رزرو کلاس"
        verbose_name_plural = "رزروهای کلاس"

    def clean(self):
        if self.fitness_class_id and self.club_id != self.fitness_class.club_id:
            raise ValidationError({"fitness_class": "کلاس متعلق به باشگاه دیگری است."})
        if self.member_id and self.club_id != self.member.club_id:
            raise ValidationError({"member": "عضو متعلق به باشگاه دیگری است."})

    def __str__(self):
        return f"{self.member} / {self.fitness_class}"
