from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class MembershipPlan(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="membership_plans", verbose_name="باشگاه")
    name = models.CharField("نام پلن", max_length=120)
    code = models.CharField("کد پلن", max_length=30)
    duration_days = models.PositiveIntegerField("مدت (روز)")
    price = models.PositiveBigIntegerField("قیمت (ریال)")
    description = models.TextField("توضیحات", blank=True)
    max_checkins = models.PositiveIntegerField("حداکثر ورود", null=True, blank=True, help_text="خالی یعنی نامحدود")
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "پلن عضویت"
        verbose_name_plural = "پلن‌های عضویت"
        constraints = [models.UniqueConstraint(fields=["club", "code"], name="uniq_plan_code_per_club")]

    def __str__(self):
        return f"{self.name} ({self.club.name})"


class MembershipContract(models.Model):
    STATUS_CHOICES = [("draft", "پیش‌نویس"), ("active", "فعال"), ("expired", "پایان‌یافته"), ("cancelled", "لغوشده")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="membership_contracts", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="membership_contracts", verbose_name="شعبه")
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="contracts", verbose_name="عضو")
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name="contracts", verbose_name="پلن")
    contract_code = models.CharField("شماره قرارداد", max_length=40)
    start_date = models.DateField("شروع")
    end_date = models.DateField("پایان")
    agreed_price = models.PositiveBigIntegerField("مبلغ قرارداد (ریال)")
    discount_amount = models.PositiveBigIntegerField("تخفیف (ریال)", default=0)
    status = models.CharField("وضعیت", max_length=12, choices=STATUS_CHOICES, default="active")
    notes = models.TextField("یادداشت", blank=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ثبت‌کننده")
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "قرارداد عضویت"
        verbose_name_plural = "قراردادهای عضویت"
        constraints = [models.UniqueConstraint(fields=["club", "contract_code"], name="uniq_contract_code_per_club")]
        indexes = [models.Index(fields=["club", "member", "status"])]

    def clean(self):
        errors = {}
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "تاریخ پایان نمی‌تواند قبل از شروع باشد."
        if self.discount_amount and self.agreed_price and self.discount_amount > self.agreed_price:
            errors["discount_amount"] = "تخفیف نمی‌تواند بیشتر از مبلغ قرارداد باشد."
        if self.member_id and self.club_id and self.member.club_id != self.club_id:
            errors["member"] = "عضو باید متعلق به همین باشگاه باشد."
        if self.plan_id and self.club_id and self.plan.club_id != self.club_id:
            errors["plan"] = "پلن باید متعلق به همین باشگاه باشد."
        if self.branch_id and self.club_id and self.branch.club_id != self.club_id:
            errors["branch"] = "شعبه باید متعلق به همین باشگاه باشد."
        if errors:
            raise ValidationError(errors)

    @property
    def balance(self):
        paid = self.payments.filter(status="paid").aggregate(total=models.Sum("amount"))["total"] or 0
        return max(0, self.agreed_price - self.discount_amount - paid)

    @property
    def is_current(self):
        today = timezone.localdate()
        return self.status == "active" and self.start_date <= today <= self.end_date

    def __str__(self):
        return f"{self.contract_code} — {self.member}"


class Payment(models.Model):
    METHOD_CHOICES = [("cash", "نقدی"), ("card", "کارت‌خوان"), ("transfer", "کارت‌به‌کارت"), ("online", "آنلاین"), ("other", "سایر")]
    STATUS_CHOICES = [("paid", "پرداخت‌شده"), ("pending", "در انتظار"), ("refunded", "مستردشده")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="membership_payments", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="membership_payments", verbose_name="شعبه")
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="payments", verbose_name="عضو")
    contract = models.ForeignKey(MembershipContract, on_delete=models.PROTECT, related_name="payments", verbose_name="قرارداد", null=True, blank=True)
    amount = models.PositiveBigIntegerField("مبلغ (ریال)")
    paid_on = models.DateField("تاریخ پرداخت", default=timezone.localdate)
    method = models.CharField("روش پرداخت", max_length=12, choices=METHOD_CHOICES, default="cash")
    status = models.CharField("وضعیت", max_length=12, choices=STATUS_CHOICES, default="paid")
    reference = models.CharField("شماره پیگیری", max_length=100, blank=True)
    notes = models.TextField("یادداشت", blank=True)
    received_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دریافت‌کننده")
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["-paid_on", "-id"]
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        indexes = [models.Index(fields=["club", "paid_on"]), models.Index(fields=["club", "member"])]

    def clean(self):
        errors = {}
        if self.member_id and self.club_id and self.member.club_id != self.club_id:
            errors["member"] = "عضو باید متعلق به همین باشگاه باشد."
        if self.contract_id:
            if self.contract.club_id != self.club_id:
                errors["contract"] = "قرارداد باید متعلق به همین باشگاه باشد."
            if self.contract.member_id != self.member_id:
                errors["contract"] = "قرارداد انتخاب‌شده متعلق به این عضو نیست."
        if self.branch_id and self.branch.club_id != self.club_id:
            errors["branch"] = "شعبه باید متعلق به همین باشگاه باشد."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.member} — {self.amount:,} ریال"
