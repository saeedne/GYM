from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class CashAccount(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="cash_accounts", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="cash_accounts", verbose_name="شعبه")
    name = models.CharField("نام صندوق/حساب", max_length=100)
    opening_balance = models.BigIntegerField("مانده آغازین (ریال)", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["club", "name"], name="uniq_cash_account_per_club")]
        verbose_name = "صندوق یا حساب"
        verbose_name_plural = "صندوق‌ها و حساب‌ها"

    def __str__(self):
        return self.name


class FinanceCategory(models.Model):
    TYPES = [("income", "درآمد"), ("expense", "هزینه")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="finance_categories", verbose_name="باشگاه")
    name = models.CharField("عنوان", max_length=100)
    entry_type = models.CharField("نوع", max_length=8, choices=TYPES)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["entry_type", "name"]
        constraints = [models.UniqueConstraint(fields=["club", "name", "entry_type"], name="uniq_finance_category_per_club_type")]
        verbose_name = "دسته مالی"
        verbose_name_plural = "دسته‌های مالی"

    def __str__(self):
        return f"{self.get_entry_type_display()} — {self.name}"


class FinanceEntry(models.Model):
    TYPES = [("income", "درآمد"), ("expense", "هزینه")]
    SOURCES = [("manual", "ثبت دستی"), ("membership_payment", "پرداخت عضویت"), ("store_sale", "فروشگاه"), ("cafe_order", "کافی‌شاپ")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="finance_entries", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="finance_entries", verbose_name="شعبه")
    account = models.ForeignKey(CashAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name="entries", verbose_name="صندوق/حساب")
    category = models.ForeignKey(FinanceCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="entries", verbose_name="دسته")
    entry_type = models.CharField("نوع", max_length=8, choices=TYPES)
    amount = models.PositiveBigIntegerField("مبلغ (ریال)")
    occurred_on = models.DateField("تاریخ", default=timezone.localdate)
    description = models.CharField("شرح", max_length=220)
    source = models.CharField("منبع", max_length=24, choices=SOURCES, default="manual")
    source_id = models.CharField("شناسه مرجع", max_length=64, blank=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["-occurred_on", "-id"]
        indexes = [models.Index(fields=["club", "occurred_on", "entry_type"])]
        constraints = [
            models.UniqueConstraint(fields=["club", "source", "source_id"], condition=~Q(source_id=""), name="uniq_finance_source_record"),
        ]
        verbose_name = "سند مالی"
        verbose_name_plural = "سندهای مالی"

    def clean(self):
        errors = {}
        if self.branch_id and self.branch.club_id != self.club_id:
            errors["branch"] = "شعبه متعلق به باشگاه دیگری است."
        if self.account_id and self.account.club_id != self.club_id:
            errors["account"] = "صندوق متعلق به باشگاه دیگری است."
        if self.category_id:
            if self.category.club_id != self.club_id:
                errors["category"] = "دسته متعلق به باشگاه دیگری است."
            elif self.category.entry_type != self.entry_type:
                errors["category"] = "نوع دسته با نوع سند هماهنگ نیست."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.get_entry_type_display()} {self.amount:,} ریال — {self.description}"
