import secrets
import jdatetime
from django import forms
from django.utils import timezone
from .models import AccessCredential, AccessPolicy, GuestPass


class CredentialForm(forms.ModelForm):
    class Meta:
        model = AccessCredential
        fields = ["member", "credential_type", "token", "is_active"]
        widgets = {"token": forms.TextInput(attrs={"autocomplete": "off"})}

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club:
            self.instance.club = club
        self.fields["member"].queryset = club.members.all() if club else self.fields["member"].queryset.none()

    def clean_token(self):
        token = self.cleaned_data["token"].strip()
        qs = AccessCredential.objects.filter(club=self.club, token=token)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("این شناسه قبلاً در این باشگاه ثبت شده است.")
        return token

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        if commit:
            obj.save()
        return obj


class GuestPassForm(forms.ModelForm):
    valid_on_jalali = forms.CharField(label="تاریخ اعتبار شمسی", widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))

    class Meta:
        model = GuestPass
        fields = ["host_member", "guest_name", "guest_mobile", "branch", "valid_on_jalali"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club:
            self.instance.club = club
        self.fields["host_member"].queryset = club.members.filter(status="active") if club else self.fields["host_member"].queryset.none()
        self.fields["branch"].queryset = club.branches.filter(is_active=True) if club else self.fields["branch"].queryset.none()
        if not self.is_bound:
            self.fields["valid_on_jalali"].initial = jdatetime.date.fromgregorian(date=timezone.localdate()).strftime("%Y/%m/%d")

    def clean_valid_on_jalali(self):
        raw = self.cleaned_data["valid_on_jalali"]
        try:
            y, m, d = map(int, raw.replace("-", "/").split("/")[:3])
            return jdatetime.date(y, m, d).togregorian()
        except (ValueError, TypeError):
            raise forms.ValidationError("تاریخ شمسی معتبر نیست.")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        obj.valid_on = self.cleaned_data["valid_on_jalali"]
        if not obj.pass_code:
            obj.pass_code = secrets.token_hex(6).upper()
        if commit:
            obj.save()
        return obj


class AccessPolicyForm(forms.ModelForm):
    allowed_weekdays = forms.CharField(label="روزهای مجاز (۰ تا ۶)", required=False)
    class Meta:
        model = AccessPolicy
        fields = ["opening_time", "closing_time", "allowed_weekdays", "enforce_hours", "enforce_days"]
        widgets = {"allowed_weekdays": forms.TextInput(attrs={"placeholder": "مثال: 0,1,2,3,4,5,6"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and self.instance.pk:
            self.fields["allowed_weekdays"].initial = ",".join(str(x) for x in self.instance.allowed_weekdays)

    def clean_allowed_weekdays(self):
        raw = self.cleaned_data.get("allowed_weekdays")
        if isinstance(raw, list):
            return raw
        try:
            values = sorted(set(int(x.strip()) for x in (raw or "").split(",") if x.strip()))
        except ValueError:
            raise forms.ValidationError("روزها را با اعداد ۰ تا ۶ و جداشده با ویرگول وارد کنید.")
        if any(x < 0 or x > 6 for x in values):
            raise forms.ValidationError("شماره روز باید بین ۰ تا ۶ باشد.")
        return values

    def clean(self):
        data = super().clean()
        if data.get("enforce_days") and not data.get("allowed_weekdays"):
            self.add_error("allowed_weekdays", "برای اعمال محدودیت روز، حداقل یک روز انتخاب کن.")
        if data.get("enforce_hours") and (not data.get("opening_time") or not data.get("closing_time")):
            self.add_error("opening_time", "برای اعمال ساعت، زمان شروع و پایان را وارد کن.")
        return data
