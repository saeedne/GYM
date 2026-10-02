import jdatetime
from django import forms
from django.utils import timezone
from .models import MembershipContract, MembershipPlan, Payment


class JalaliDateMixin:
    def set_jalali(self, field_name, value):
        if value:
            self.fields[field_name].initial = jdatetime.date.fromgregorian(date=value).strftime("%Y/%m/%d")

    def clean_jalali(self, name):
        raw = (self.cleaned_data.get(name) or "").strip()
        if not raw:
            raise forms.ValidationError("این تاریخ الزامی است.")
        try:
            y, m, d = map(int, raw.replace("-", "/").split("/")[:3])
            return jdatetime.date(y, m, d).togregorian()
        except (ValueError, TypeError):
            raise forms.ValidationError("تاریخ شمسی معتبر نیست.")


class MembershipPlanForm(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = ["name", "code", "duration_days", "price", "max_checkins", "description", "is_active"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        qs = MembershipPlan.objects.filter(club=self.club, code=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("این کد در باشگاه فعال است.")
        return code

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        if commit:
            obj.save()
        return obj


class ContractForm(JalaliDateMixin, forms.ModelForm):
    start_date_jalali = forms.CharField(label="تاریخ شروع شمسی", widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))
    end_date_jalali = forms.CharField(label="تاریخ پایان شمسی", widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))

    class Meta:
        model = MembershipContract
        fields = ["member", "plan", "branch", "contract_code", "start_date_jalali", "end_date_jalali", "agreed_price", "discount_amount", "status", "notes"]

    def clean_start_date_jalali(self):
        return self.clean_jalali("start_date_jalali")

    def clean_end_date_jalali(self):
        return self.clean_jalali("end_date_jalali")

    def __init__(self, *args, club=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club, self.user = club, user
        self.fields["member"].queryset = club.members.all() if club else self.fields["member"].queryset.none()
        self.fields["plan"].queryset = club.membership_plans.filter(is_active=True) if club else self.fields["plan"].queryset.none()
        self.fields["branch"].queryset = club.branches.filter(is_active=True) if club else self.fields["branch"].queryset.none()
        if self.instance.pk:
            self.set_jalali("start_date_jalali", self.instance.start_date)
            self.set_jalali("end_date_jalali", self.instance.end_date)
        if not self.is_bound and not self.instance.pk:
            today = timezone.localdate()
            self.fields["start_date_jalali"].initial = jdatetime.date.fromgregorian(date=today).strftime("%Y/%m/%d")

    def clean_contract_code(self):
        value = self.cleaned_data["contract_code"].strip()
        qs = MembershipContract.objects.filter(club=self.club, contract_code=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("شماره قرارداد تکراری است.")
        return value

    def clean(self):
        data = super().clean()
        data["start_date"] = data.get("start_date_jalali")
        data["end_date"] = data.get("end_date_jalali")
        plan = data.get("plan")
        if plan and not self.instance.pk and not data.get("agreed_price"):
            data["agreed_price"] = plan.price
        if data.get("start_date") and data.get("end_date") and data["end_date"] < data["start_date"]:
            self.add_error("end_date_jalali", "تاریخ پایان نمی‌تواند قبل از شروع باشد.")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        obj.start_date = self.cleaned_data["start_date"]
        obj.end_date = self.cleaned_data["end_date"]
        if not obj.agreed_price:
            obj.agreed_price = obj.plan.price
        obj.created_by = obj.created_by or self.user
        if obj.branch_id and obj.branch.club_id != self.club.id:
            obj.branch = None
        if commit:
            obj.save()
        return obj


class PaymentForm(JalaliDateMixin, forms.ModelForm):
    paid_on_jalali = forms.CharField(label="تاریخ پرداخت شمسی", required=False, widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))

    class Meta:
        model = Payment
        fields = ["member", "contract", "branch", "amount", "paid_on_jalali", "method", "status", "reference", "notes"]

    def __init__(self, *args, club=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club, self.user = club, user
        self.fields["member"].queryset = club.members.all() if club else self.fields["member"].queryset.none()
        self.fields["contract"].queryset = club.membership_contracts.all() if club else self.fields["contract"].queryset.none()
        self.fields["branch"].queryset = club.branches.filter(is_active=True) if club else self.fields["branch"].queryset.none()
        if self.instance.pk:
            self.set_jalali("paid_on_jalali", self.instance.paid_on)
        elif not self.is_bound:
            self.fields["paid_on_jalali"].initial = jdatetime.date.fromgregorian(date=timezone.localdate()).strftime("%Y/%m/%d")

    def clean(self):
        data = super().clean()
        raw = (data.get("paid_on_jalali") or "").strip()
        if raw:
            try:
                y, m, d = map(int, raw.replace("-", "/").split("/")[:3])
                data["paid_on"] = jdatetime.date(y, m, d).togregorian()
            except (ValueError, TypeError):
                self.add_error("paid_on_jalali", "تاریخ شمسی معتبر نیست.")
        else:
            data["paid_on"] = timezone.localdate()
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        obj.paid_on = self.cleaned_data["paid_on"]
        obj.received_by = self.user
        if commit:
            obj.save()
        return obj
