from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Permission
from django.db import models
from .access import ROLE_PERMISSION_CHOICES


class User(AbstractUser):
    display_name = models.CharField("نام نمایشی", max_length=120, blank=True)

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.display_name or self.get_full_name() or self.username


class ClubRole(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="roles", verbose_name="باشگاه")
    name = models.CharField("عنوان نقش", max_length=100)
    description = models.CharField("توضیح", max_length=240, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="club_roles", verbose_name="دسترسی‌ها")
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "نقش باشگاه"
        verbose_name_plural = "نقش‌های باشگاه"
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["club", "name"], name="uniq_role_name_per_club")]
        permissions = ROLE_PERMISSION_CHOICES

    def __str__(self):
        return f"{self.name} — {self.club.name}"


class ClubMembership(models.Model):
    user = models.ForeignKey(User, verbose_name="کاربر", on_delete=models.CASCADE, related_name="club_memberships")
    club = models.ForeignKey("core.Club", verbose_name="باشگاه", on_delete=models.CASCADE, related_name="user_memberships")
    branch = models.ForeignKey(
        "core.Branch",
        verbose_name="شعبه پیش‌فرض",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_memberships",
    )
    role = models.CharField("نقش در باشگاه", max_length=80, blank=True)
    club_role = models.ForeignKey(ClubRole, verbose_name="سطح دسترسی", on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    direct_permissions = models.ManyToManyField(Permission, blank=True, related_name="direct_club_memberships", verbose_name="دسترسی‌های اختصاصی")
    webapp_enabled = models.BooleanField("دسترسی به Web App", default=True)
    is_manager = models.BooleanField("مدیر این باشگاه", default=False)
    is_active = models.BooleanField("عضویت فعال", default=True)
    joined_at = models.DateTimeField("تاریخ عضویت", auto_now_add=True)

    class Meta:
        verbose_name = "عضویت کاربر در باشگاه"
        verbose_name_plural = "عضویت‌های کاربران در باشگاه‌ها"
        constraints = [
            models.UniqueConstraint(fields=["user", "club"], name="uniq_user_club_membership"),
        ]

    def clean(self):
        if self.club_role_id and self.club_id and self.club_role.club_id != self.club_id:
            from django.core.exceptions import ValidationError
            raise ValidationError({"club_role": "این نقش متعلق به باشگاه دیگری است."})

    def __str__(self):
        return f"{self.user} / {self.club}"
