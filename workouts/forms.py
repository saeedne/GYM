import jdatetime
from django import forms
from django.utils import timezone
from .models import BodyAssessment, Exercise, PlanExercise, WorkoutAssignment, WorkoutPlan


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ["name", "muscle_group", "equipment", "instructions", "is_active"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        if commit: obj.save()
        return obj


class PlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ["name", "level", "trainer", "description", "is_active"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        self.fields["trainer"].queryset = club.trainers.filter(is_active=True) if club else self.fields["trainer"].queryset.none()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        if commit: obj.save()
        return obj


class PlanExerciseForm(forms.ModelForm):
    class Meta:
        model = PlanExercise
        fields = ["exercise", "day_number", "sets", "repetitions", "rest_seconds", "sort_order", "notes"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exercise"].queryset = club.exercises.filter(is_active=True) if club else Exercise.objects.none()


class AssignmentForm(forms.ModelForm):
    start_date_jalali = forms.CharField(label="تاریخ شروع شمسی", widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))
    end_date_jalali = forms.CharField(label="تاریخ پایان شمسی", required=False, widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))

    class Meta:
        model = WorkoutAssignment
        fields = ["member", "plan", "start_date_jalali", "end_date_jalali", "is_active", "notes"]

    def __init__(self, *args, club=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club, self.user = club, user
        self.fields["member"].queryset = club.members.all() if club else self.fields["member"].queryset.none()
        self.fields["plan"].queryset = club.workout_plans.filter(is_active=True) if club else self.fields["plan"].queryset.none()
        if self.instance.pk:
            self.fields["start_date_jalali"].initial = jdatetime.date.fromgregorian(date=self.instance.start_date).strftime("%Y/%m/%d")
            if self.instance.end_date:
                self.fields["end_date_jalali"].initial = jdatetime.date.fromgregorian(date=self.instance.end_date).strftime("%Y/%m/%d")
        elif not self.is_bound:
            self.fields["start_date_jalali"].initial = jdatetime.date.fromgregorian(date=timezone.localdate()).strftime("%Y/%m/%d")

    def _parse(self, key, required):
        raw = (self.cleaned_data.get(key) or "").strip()
        if not raw and not required: return None
        try:
            y, m, d = map(int, raw.replace("-", "/").split("/")[:3])
            return jdatetime.date(y, m, d).togregorian()
        except (ValueError, TypeError):
            raise forms.ValidationError("تاریخ شمسی معتبر نیست.")

    def clean_start_date_jalali(self): return self._parse("start_date_jalali", True)
    def clean_end_date_jalali(self): return self._parse("end_date_jalali", False)

    def clean(self):
        data = super().clean()
        if data.get("start_date_jalali") and data.get("end_date_jalali") and data["end_date_jalali"] < data["start_date_jalali"]:
            self.add_error("end_date_jalali", "پایان برنامه باید پس از شروع باشد.")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        obj.start_date = self.cleaned_data["start_date_jalali"]
        obj.end_date = self.cleaned_data.get("end_date_jalali")
        obj.assigned_by = self.user
        if commit: obj.save()
        return obj


class AssessmentForm(forms.ModelForm):
    measured_on_jalali = forms.CharField(label="تاریخ ارزیابی شمسی", widget=forms.TextInput(attrs={"class": "jalali-date", "autocomplete": "off"}))

    class Meta:
        model = BodyAssessment
        fields = ["member", "branch", "measured_on_jalali", "height_cm", "weight_kg", "body_fat_percent", "waist_cm", "chest_cm", "notes"]

    def __init__(self, *args, club=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club, self.user = club, user
        self.fields["member"].queryset = club.members.all() if club else self.fields["member"].queryset.none()
        self.fields["branch"].queryset = club.branches.filter(is_active=True) if club else self.fields["branch"].queryset.none()
        if self.instance.pk:
            self.fields["measured_on_jalali"].initial = jdatetime.date.fromgregorian(date=self.instance.measured_on).strftime("%Y/%m/%d")
        elif not self.is_bound:
            self.fields["measured_on_jalali"].initial = jdatetime.date.fromgregorian(date=timezone.localdate()).strftime("%Y/%m/%d")

    def clean_measured_on_jalali(self):
        raw = self.cleaned_data["measured_on_jalali"]
        try:
            y, m, d = map(int, raw.replace("-", "/").split("/")[:3])
            return jdatetime.date(y, m, d).togregorian()
        except (ValueError, TypeError):
            raise forms.ValidationError("تاریخ شمسی معتبر نیست.")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        obj.measured_on = self.cleaned_data["measured_on_jalali"]
        obj.assessed_by = self.user
        if commit: obj.save()
        return obj
