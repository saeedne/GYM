from django.db import models


class Club(models.Model):
    STATUS_CHOICES = [
        ("active", "فعال"),
        ("suspended", "معلق"),
        ("archived", "بایگانی"),
    ]

    name = models.CharField("نام باشگاه", max_length=160)
    code = models.CharField("کد باشگاه", max_length=40, unique=True)
    slug = models.SlugField("شناسه یکتا", max_length=80, unique=True)
    phone = models.CharField("تلفن", max_length=30, blank=True)
    email = models.EmailField("ایمیل", blank=True)
    address = models.TextField("آدرس", blank=True)
    logo = models.ImageField("لوگو", upload_to="clubs/logos/", blank=True, null=True)
    status = models.CharField("وضعیت", max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        verbose_name = "باشگاه"
        verbose_name_plural = "باشگاه‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Branch(models.Model):
    club = models.ForeignKey(Club, verbose_name="باشگاه", on_delete=models.CASCADE, related_name="branches")
    name = models.CharField("نام شعبه", max_length=120)
    code = models.CharField("کد شعبه", max_length=30)
    phone = models.CharField("تلفن", max_length=30, blank=True)
    address = models.TextField("آدرس", blank=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "شعبه"
        verbose_name_plural = "شعبه‌ها"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["club", "code"], name="uniq_branch_code_per_club"),
        ]

    def __str__(self):
        return f"{self.club.name} / {self.name}"


class SystemModule(models.Model):
    code = models.CharField("کد", max_length=50, unique=True)
    name = models.CharField("نام ماژول", max_length=100)
    icon = models.CharField("آیکن", max_length=50, default="◈")
    description = models.TextField("توضیح", blank=True)
    implemented = models.BooleanField("پیاده‌سازی شده", default=False)
    sort_order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "ماژول سیستم"
        verbose_name_plural = "ماژول‌های سیستم"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class ClubModule(models.Model):
    club = models.ForeignKey(Club, verbose_name="باشگاه", on_delete=models.CASCADE, related_name="modules")
    module = models.ForeignKey(SystemModule, verbose_name="ماژول", on_delete=models.CASCADE, related_name="club_settings")
    enabled = models.BooleanField("فعال برای این باشگاه", default=False)
    settings_json = models.JSONField("تنظیمات ماژول", default=dict, blank=True)

    class Meta:
        verbose_name = "فعال‌سازی ماژول باشگاه"
        verbose_name_plural = "فعال‌سازی ماژول‌های باشگاه"
        constraints = [
            models.UniqueConstraint(fields=["club", "module"], name="uniq_module_per_club"),
        ]

    def __str__(self):
        return f"{self.club.name} / {self.module.name}"


class AuditLog(models.Model):
    ACTIONS = [
        ("create", "ایجاد"),
        ("update", "ویرایش"),
        ("delete", "حذف"),
        ("login", "ورود"),
        ("switch_club", "تغییر باشگاه"),
    ]
    club = models.ForeignKey(Club, verbose_name="باشگاه", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    user = models.ForeignKey("accounts.User", verbose_name="کاربر", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField("عملیات", max_length=30, choices=ACTIONS)
    model_name = models.CharField("مدل", max_length=120, blank=True)
    object_id = models.CharField("شناسه شیء", max_length=80, blank=True)
    description = models.TextField("شرح", blank=True)
    created_at = models.DateTimeField("زمان", auto_now_add=True)

    class Meta:
        verbose_name = "لاگ عملیات"
        verbose_name_plural = "لاگ عملیات"
        ordering = ["-created_at"]
