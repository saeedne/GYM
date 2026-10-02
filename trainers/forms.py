import jdatetime
from django import forms
from django.utils import timezone
from .models import ClassBooking, FitnessClass, Trainer


class ClubFormMixin:
    def branch_queryset(self, club):
        return club.branches.filter(is_active=True) if club else self.fields["branch"].queryset.none()


class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ["display_name", "mobile", "branch", "specialty", "bio", "is_active"]

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


class FitnessClassForm(forms.ModelForm):
    class_date = forms.CharField(label="تاریخ شمسی کلاس", widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))
    start_time = forms.TimeField(label="ساعت شروع", widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(label="ساعت پایان", widget=forms.TimeInput(attrs={"type": "time"}))

    class Meta:
        model = FitnessClass
        fields = ["title", "branch", "trainer", "class_date", "start_time", "end_time", "capacity", "room", "description", "status"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club: self.instance.club = club
        self.fields["branch"].queryset = club.branches.filter(is_active=True) if club else self.fields["branch"].queryset.none()
        self.fields["trainer"].queryset = club.trainers.filter(is_active=True) if club else self.fields["trainer"].queryset.none()
        if self.instance.pk:
            self.fields["class_date"].initial = jdatetime.date.fromgregorian(date=timezone.localtime(self.instance.starts_at).date()).strftime("%Y/%m/%d")
            self.fields["start_time"].initial = timezone.localtime(self.instance.starts_at).strftime("%H:%M")
            self.fields["end_time"].initial = timezone.localtime(self.instance.ends_at).strftime("%H:%M")

    def clean_class_date(self):
        try:
            y, m, d = map(int, self.cleaned_data["class_date"].replace("-", "/").split("/")[:3])
            return jdatetime.date(y, m, d).togregorian()
        except (ValueError, TypeError):
            raise forms.ValidationError("تاریخ شمسی معتبر نیست.")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        date = self.cleaned_data["class_date"]
        obj.starts_at = timezone.make_aware(__import__("datetime").datetime.combine(date, self.cleaned_data["start_time"]))
        obj.ends_at = timezone.make_aware(__import__("datetime").datetime.combine(date, self.cleaned_data["end_time"]))
        if commit: obj.save()
        return obj


class BookingForm(forms.ModelForm):
    class Meta:
        model = ClassBooking
        fields = ["member"]

    def __init__(self, *args, club=None, fitness_class=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club: self.instance.club = club
        if fitness_class: self.instance.fitness_class = fitness_class
        self.fields["member"].queryset = club.members.filter(status="active") if club else self.fields["member"].queryset.none()
