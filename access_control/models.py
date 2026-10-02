from django.core.exceptions import ValidationError
from django.db import models


class AccessPolicy(models.Model):
    club = models.OneToOneField("core.Club", on_delete=models.CASCADE, related_name="access_policy", verbose_name="باشگاه")
    opening_time = models.TimeField("شروع مجاز ورود", null=True, blank=True)
    closing_time = models.TimeField("پایان مجاز ورود", null=True, blank=True)
    allowed_weekdays = models.JSONField("روزهای مجاز هفته", default=list, blank=True, help_text="۰ شنبه، ۶ جمعه؛ خالی یعنی همه روزها")
    enforce_hours = models.BooleanField("اعمال ساعت مجاز", default=False)
    enforce_days = models.BooleanField("اعمال روزهای مجاز", default=False)

    def clean(self):
        if self.opening_time and self.closing_time and self.closing_time <= self.opening_time:
            raise ValidationError({"closing_time": "ساعت پایان باید بعد از ساعت شروع باشد."})

    def __str__(self):
        return f"قوانین ورود {self.club.name}"


class AccessCredential(models.Model):
    TYPES = [("qr", "QR"), ("rfid", "RFID"), ("card", "کارت"), ("pin", "کد دستی")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="access_credentials", verbose_name="باشگاه")
    member = models.ForeignKey("members.Member", on_delete=models.CASCADE, related_name="access_credentials", verbose_name="عضو")
    credential_type = models.CharField("نوع شناسه", max_length=8, choices=TYPES, default="qr")
    token = models.CharField("کد/توکن", max_length=160)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)
    last_used_at = models.DateTimeField("آخرین استفاده", null=True, blank=True)

    class Meta:
        ordering = ["member__last_name", "member__first_name"]
        constraints = [
            models.UniqueConstraint(fields=["club", "token"], name="uniq_access_token_per_club"),
        ]
        indexes = [models.Index(fields=["club", "token", "is_active"])]
        verbose_name = "شناسه ورود"
        verbose_name_plural = "شناسه‌های ورود"

    def clean(self):
        if self.member_id and self.club_id and self.member.club_id != self.club_id:
            raise ValidationError({"member": "عضو باید متعلق به همین باشگاه باشد."})

    def __str__(self):
        return f"{self.get_credential_type_display()} — {self.member}"


class GuestPass(models.Model):
    STATUS = [("issued", "صادرشده"), ("used", "استفاده‌شده"), ("cancelled", "لغوشده")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="guest_passes", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="شعبه")
    host_member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="guest_passes", verbose_name="عضو میزبان")
    guest_name = models.CharField("نام مهمان", max_length=120)
    guest_mobile = models.CharField("موبایل مهمان", max_length=20, blank=True)
    pass_code = models.CharField("کد مهمان", max_length=40)
    valid_on = models.DateField("تاریخ اعتبار")
    status = models.CharField("وضعیت", max_length=12, choices=STATUS, default="issued")
    checked_in_at = models.DateTimeField("زمان ورود", null=True, blank=True)
    created_at = models.DateTimeField("صدور", auto_now_add=True)

    class Meta:
        ordering = ["-valid_on", "-id"]
        constraints = [models.UniqueConstraint(fields=["club", "pass_code"], name="uniq_guest_pass_per_club")]
        verbose_name = "مجوز مهمان"
        verbose_name_plural = "مجوزهای مهمان"

    def clean(self):
        if self.host_member_id and self.host_member.club_id != self.club_id:
            raise ValidationError({"host_member": "عضو میزبان باید متعلق به همین باشگاه باشد."})
        if self.branch_id and self.branch.club_id != self.club_id:
            raise ValidationError({"branch": "شعبه باید متعلق به همین باشگاه باشد."})

    def __str__(self):
        return f"{self.guest_name} ({self.pass_code})"
