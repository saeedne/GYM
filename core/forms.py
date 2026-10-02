from django import forms
from .models import Branch, Club


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["name", "code", "slug", "phone", "email", "address", "status", "logo"]


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ["name", "code", "phone", "address", "is_active"]

    def __init__(self, *args, club, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club

    def save(self, commit=True):
        branch = super().save(commit=False)
        branch.club = self.club
        if commit:
            branch.save()
        return branch
