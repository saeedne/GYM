from django import forms
from .models import InventoryMovement, Product, StoreSale


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["branch", "sku", "name", "category", "unit", "cost_price", "sale_price", "stock_quantity", "min_stock", "is_active"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club: self.instance.club = club
        self.fields["branch"].queryset = club.branches.filter(is_active=True) if club else self.fields["branch"].queryset.none()

    def save(self, commit=True):
        item = super().save(commit=False)
        item.club = self.club
        if commit: item.save()
        return item


class SaleForm(forms.ModelForm):
    class Meta:
        model = StoreSale
        fields = ["branch", "product", "member", "quantity"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club: self.instance.club = club
        if club:
            self.fields["branch"].queryset = club.branches.filter(is_active=True)
            self.fields["product"].queryset = club.store_products.filter(is_active=True)
            self.fields["member"].queryset = club.members.all()


class StockForm(forms.Form):
    product = forms.ModelChoiceField(label="کالا", queryset=Product.objects.none())
    movement_type = forms.ChoiceField(label="نوع گردش", choices=InventoryMovement.TYPES)
    quantity = forms.IntegerField(label="تعداد", min_value=1)
    reason = forms.CharField(label="شرح", max_length=180, required=False)

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = club.store_products.all() if club else Product.objects.none()
