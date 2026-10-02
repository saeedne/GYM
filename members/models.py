from django.db import models


class Member(models.Model):
    STATUS_CHOICES = [
        ("active", "فعال"),
        ("inactive", "غیرفعال"),
        ("suspended", "معلق"),
        ("blocked", "مسدود"),
    ]
    GENDER_CHOICES = [
        ("male", "مرد"),
        ("female", "زن"),
        ("other", "سایر"),
    ]

    club = models.ForeignKey("core.Club", verbose_name="باشگاه", on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey("accounts.User", verbose_name="حساب ورود عضو", on_delete=models.SET_NULL, null=True, blank=True, related_name="member_profiles")
    branch = models.ForeignKey(
        "core.Branch",
        verbose_name="شعبه",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    member_code = models.CharField("کد عضویت", max_length=30)
    first_name = models.CharField("نام", max_length=80)
    last_name = models.CharField("نام خانوادگی", max_length=100)
    national_id = models.CharField("کد ملی", max_length=20, blank=True)
    mobile = models.CharField("موبایل", max_length=20)
    email = models.EmailField("ایمیل", blank=True)
    birth_date = models.DateField("تاریخ تولد", null=True, blank=True)
    gender = models.CharField("جنسیت", max_length=10, choices=GENDER_CHOICES, blank=True)
    emergency_name = models.CharField("نام تماس اضطراری", max_length=120, blank=True)
    emergency_mobile = models.CharField("موبایل اضطراری", max_length=20, blank=True)
    status = models.CharField("وضعیت", max_length=20, choices=STATUS_CHOICES, default="active")
    photo = models.ImageField("عکس", upload_to="members/photos/", blank=True, null=True)
    notes = models.TextField("یادداشت", blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "عضو"
        verbose_name_plural = "اعضا"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["club", "member_code"], name="uniq_member_code_per_club"),
            models.UniqueConstraint(fields=["club", "user"], condition=models.Q(user__isnull=False), name="uniq_member_user_per_club"),
        ]
        indexes = [
            models.Index(fields=["club", "mobile"]),
            models.Index(fields=["club", "national_id"]),
            models.Index(fields=["club", "status"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
