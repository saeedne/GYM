import jdatetime
from django import forms
from .models import Member


class MemberForm(forms.ModelForm):
    birth_date_jalali = forms.CharField(
        label="تاریخ تولد",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "jalali-date",
            "autocomplete": "off",
            "placeholder": "۱۴۰۰/۰۱/۰۱",
        }),
    )

    class Meta:
        model = Member
        fields = [
            "branch", "member_code", "first_name", "last_name", "national_id",
            "mobile", "email", "birth_date_jalali", "gender",
            "emergency_name", "emergency_mobile", "status", "photo", "notes",
        ]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club:
            self.fields["branch"].queryset = club.branches.filter(is_active=True)

        if self.instance and self.instance.birth_date:
            self.fields["birth_date_jalali"].initial = jdatetime.date.fromgregorian(
                date=self.instance.birth_date
            ).strftime("%Y/%m/%d")

    def clean_member_code(self):
        value = self.cleaned_data["member_code"].strip()
        qs = Member.objects.filter(club=self.club, member_code=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("این کد عضویت قبلاً در این باشگاه استفاده شده است.")
        return value

    def clean(self):
        cleaned = super().clean()
        raw = (cleaned.get("birth_date_jalali") or "").strip()
        if raw:
            try:
                y, m, d = [int(x) for x in raw.replace("-", "/").split("/")[:3]]
                cleaned["birth_date"] = jdatetime.date(y, m, d).togregorian()
            except Exception:
                self.add_error("birth_date_jalali", "تاریخ جلالی معتبر نیست.")
        else:
            cleaned["birth_date"] = None
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.birth_date = self.cleaned_data.get("birth_date")
        obj.club = self.club
        if commit:
            obj.save()
        return obj
