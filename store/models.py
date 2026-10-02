from django.core.exceptions import ValidationError
from django.db import models


class Product(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="store_products", verbose_name="باشگاه")
    branch = models.ForeignKey("core.Branch", on_delete=models.PROTECT, related_name="store_products", verbose_name="شعبه")
    sku = models.CharField("کد کالا", max_length=40)
    name = models.CharField("نام کالا", max_length=140)
    category = models.CharField("دسته", max_length=80, blank=True)
    unit = models.CharField("واحد", max_length=30, default="عدد")
    cost_price = models.PositiveBigIntegerField("قیمت خرید (ریال)", default=0)
    sale_price = models.PositiveBigIntegerField("قیمت فروش (ریال)")
    stock_quantity = models.PositiveIntegerField("موجودی")
    min_stock = models.PositiveIntegerField("حداقل موجودی", default=0)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["club", "sku"], name="uniq_store_sku_per_club")]
        indexes = [models.Index(fields=["club", "stock_quantity"])]
        verbose_name = "کالای فروشگاه"
        verbose_name_plural = "کالاهای فروشگاه"

    def clean(self):
        if self.branch_id and self.branch.club_id != self.club_id:
            raise ValidationError({"branch": "شعبه متعلق به باشگاه دیگری است."})

    @property
    def low_stock(self):
        return self.stock_quantity <= self.min_stock

    def __str__(self):
        return f"{self.name} ({self.sku})"


class InventoryMovement(models.Model):
    TYPES = [("in", "افزایش"), ("out", "کاهش")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="inventory_movements")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements", verbose_name="کالا")
    movement_type = models.CharField("نوع", max_length=3, choices=TYPES)
    quantity = models.PositiveIntegerField("تعداد")
    reason = models.CharField("شرح", max_length=180, blank=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField("زمان", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "گردش موجودی"
        verbose_name_plural = "گردش موجودی"

    def clean(self):
        if self.product_id and self.product.club_id != self.club_id:
            raise ValidationError({"product": "کالا متعلق به باشگاه دیگری است."})


class StoreSale(models.Model):
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="store_sales")
    branch = models.ForeignKey("core.Branch", on_delete=models.PROTECT, related_name="store_sales", verbose_name="شعبه")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sales", verbose_name="کالا")
    member = models.ForeignKey("members.Member", on_delete=models.SET_NULL, null=True, blank=True, related_name="store_sales", verbose_name="عضو")
    quantity = models.PositiveIntegerField("تعداد")
    unit_price = models.PositiveBigIntegerField("قیمت واحد (ریال)")
    sold_at = models.DateTimeField("زمان فروش", auto_now_add=True)
    received_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-sold_at"]
        indexes = [models.Index(fields=["club", "sold_at"])]
        verbose_name = "فروش فروشگاه"
        verbose_name_plural = "فروش‌های فروشگاه"

    @property
    def total(self):
        return self.quantity * self.unit_price

    def clean(self):
        if self.product_id and self.product.club_id != self.club_id:
            raise ValidationError({"product": "کالا متعلق به باشگاه دیگری است."})
        if self.member_id and self.member.club_id != self.club_id:
            raise ValidationError({"member": "عضو متعلق به باشگاه دیگری است."})
        if self.branch_id and self.branch.club_id != self.club_id:
            raise ValidationError({"branch": "شعبه متعلق به باشگاه دیگری است."})
