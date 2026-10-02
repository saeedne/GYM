import jdatetime
from django import forms
from django.utils import timezone
from core.models import Branch


class CheckInForm(forms.Form):
    credential_value = forms.CharField(label="کد عضویت / کارت / QR", max_length=160, widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "کد را وارد یا اسکن کنید", "autocomplete": "off"}))
    branch = forms.ModelChoiceField(label="شعبه", queryset=Branch.objects.none(), required=False)

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club:
            self.fields["branch"].queryset = club.branches.filter(is_active=True)


def parse_jalali_date(raw):
    if not raw:
        return None
    try:
        y, m, d = map(int, raw.replace("-", "/").split("/")[:3])
        return jdatetime.date(y, m, d).togregorian()
    except (ValueError, TypeError):
        raise forms.ValidationError("تاریخ شمسی معتبر نیست.")


class AttendanceReportFilter(forms.Form):
    date_from = forms.CharField(label="از تاریخ شمسی", required=False, widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))
    date_to = forms.CharField(label="تا تاریخ شمسی", required=False, widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))

    def clean(self):
        data = super().clean()
        try:
            data["start"] = parse_jalali_date(data.get("date_from", ""))
        except forms.ValidationError as e:
            self.add_error("date_from", e)
        try:
            data["end"] = parse_jalali_date(data.get("date_to", ""))
        except forms.ValidationError as e:
            self.add_error("date_to", e)
        if data.get("start") and data.get("end") and data["end"] < data["start"]:
            self.add_error("date_to", "تاریخ پایان باید پس از تاریخ شروع باشد.")
        return data

    def initial_today(self):
        today = jdatetime.date.fromgregorian(date=timezone.localdate()).strftime("%Y/%m/%d")
        self.fields["date_from"].initial = today
        self.fields["date_to"].initial = today
