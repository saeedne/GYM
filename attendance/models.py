from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [("open", "داخل باشگاه"), ("closed", "خروج ثبت‌شده"), ("denied", "ورود غیرمجاز")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="attendance_records", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_records", verbose_name="شعبه")
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="attendance_records", verbose_name="عضو")
    check_in = models.DateTimeField("زمان ورود")
    check_out = models.DateTimeField("زمان خروج", null=True, blank=True)
    status = models.CharField("وضعیت", max_length=10, choices=STATUS_CHOICES, default="open")
    denial_reason = models.CharField("علت عدم پذیرش", max_length=200, blank=True)
    source = models.CharField("منبع ثبت", max_length=30, default="reception")
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ثبت‌کننده")
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["-check_in"]
        verbose_name = "تردد عضو"
        verbose_name_plural = "تردد اعضا"
        indexes = [models.Index(fields=["club", "check_in"]), models.Index(fields=["club", "status"])]
        constraints = [
            models.UniqueConstraint(fields=["club", "member"], condition=Q(status="open"), name="uniq_open_visit_per_member_club"),
        ]

    def clean(self):
        errors = {}
        if self.member_id and self.club_id and self.member.club_id != self.club_id:
            errors["member"] = "عضو باید متعلق به همین باشگاه باشد."
        if self.branch_id and self.club_id and self.branch.club_id != self.club_id:
            errors["branch"] = "شعبه باید متعلق به همین باشگاه باشد."
        if self.check_in and self.check_out and self.check_out < self.check_in:
            errors["check_out"] = "زمان خروج نمی‌تواند قبل از ورود باشد."
        if self.status == "open" and self.check_out:
            errors["status"] = "رکورد دارای زمان خروج نمی‌تواند باز باشد."
        if self.status == "closed" and not self.check_out:
            errors["status"] = "برای تردد بسته، زمان خروج لازم است."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.member} — {self.check_in:%Y-%m-%d %H:%M}"
