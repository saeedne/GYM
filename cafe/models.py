from django.core.exceptions import ValidationError
from django.db import models


class MenuItem(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="cafe_menu", verbose_name="باشگاه")
    name = models.CharField("نام محصول", max_length=120)
    category = models.CharField("دسته", max_length=80, blank=True)
    price = models.PositiveBigIntegerField("قیمت (ریال)")
    is_available = models.BooleanField("موجود در منو", default=True)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["category", "name"]
        constraints = [models.UniqueConstraint(fields=["club", "name"], name="uniq_cafe_item_per_club")]
        verbose_name = "محصول کافی‌شاپ"
        verbose_name_plural = "منوی کافی‌شاپ"

    def __str__(self):
        return self.name


class CafeOrder(models.Model):
    STATUS = [("open", "در حال آماده‌سازی"), ("ready", "آماده"), ("served", "تحویل‌شده"), ("cancelled", "لغوشده")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="cafe_orders")
    branch = models.ForeignKey("core.Branch", on_delete=models.PROTECT, related_name="cafe_orders", verbose_name="شعبه")
    member = models.ForeignKey("members.Member", on_delete=models.SET_NULL, null=True, blank=True, related_name="cafe_orders", verbose_name="عضو")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name="orders", verbose_name="محصول")
    quantity = models.PositiveSmallIntegerField("تعداد", default=1)
    unit_price = models.PositiveBigIntegerField("قیمت واحد (ریال)")
    status = models.CharField("وضعیت", max_length=12, choices=STATUS, default="open")
    notes = models.CharField("یادداشت", max_length=180, blank=True)
    ordered_at = models.DateTimeField("زمان سفارش", auto_now_add=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-ordered_at"]
        indexes = [models.Index(fields=["club", "ordered_at"])]
        verbose_name = "سفارش کافی‌شاپ"
        verbose_name_plural = "سفارش‌های کافی‌شاپ"

    @property
    def total(self):
        return self.quantity * self.unit_price

    def clean(self):
        errors = {}
        if self.menu_item_id and self.menu_item.club_id != self.club_id:
            errors["menu_item"] = "محصول متعلق به باشگاه دیگری است."
        if self.member_id and self.member.club_id != self.club_id:
            errors["member"] = "عضو متعلق به باشگاه دیگری است."
        if self.branch_id and self.branch.club_id != self.club_id:
            errors["branch"] = "شعبه متعلق به باشگاه دیگری است."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.menu_item} × {self.quantity}"
