import jdatetime
from django import forms
from .models import CashAccount, FinanceCategory, FinanceEntry


class FinanceEntryForm(forms.ModelForm):
    occurred_on_jalali = forms.CharField(label="تاریخ شمسی", widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))

    class Meta:
        model = FinanceEntry
        fields = ["entry_type", "branch", "account", "category", "amount", "occurred_on_jalali", "description"]

    def __init__(self, *args, club=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club, self.user = club, user
        if club: self.instance.club = club
        if club:
            self.fields["branch"].queryset = club.branches.filter(is_active=True)
            self.fields["account"].queryset = club.cash_accounts.filter(is_active=True)
            self.fields["category"].queryset = club.finance_categories.filter(is_active=True)
        if not self.is_bound:
            from django.utils import timezone
            self.fields["occurred_on_jalali"].initial = jdatetime.date.fromgregorian(date=timezone.localdate()).strftime("%Y/%m/%d")

    def clean_occurred_on_jalali(self):
        raw = self.cleaned_data["occurred_on_jalali"]
        try:
            y, m, d = map(int, raw.replace("-", "/").split("/")[:3])
            return jdatetime.date(y, m, d).togregorian()
        except (ValueError, TypeError):
            raise forms.ValidationError("تاریخ شمسی معتبر نیست.")

    def clean(self):
        data = super().clean()
        category = data.get("category")
        if category and data.get("entry_type") and category.entry_type != data["entry_type"]:
            self.add_error("category", "دسته انتخابی با نوع سند هماهنگ نیست.")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club, obj.created_by = self.club, self.user
        obj.occurred_on = self.cleaned_data["occurred_on_jalali"]
        if commit: obj.save()
        return obj


class CashAccountForm(forms.ModelForm):
    class Meta:
        model = CashAccount
        fields = ["branch", "name", "opening_balance", "is_active"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club: self.instance.club = club
        self.fields["branch"].queryset = club.branches.filter(is_active=True) if club else self.fields["branch"].queryset.none()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        if commit: obj.save()
        return obj


class CategoryForm(forms.ModelForm):
    class Meta:
        model = FinanceCategory
        fields = ["name", "entry_type", "is_active"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club: self.instance.club = club

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        if commit: obj.save()
        return obj
