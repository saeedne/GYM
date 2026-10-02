from django import forms
from .models import CafeOrder, MenuItem


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["name", "category", "price", "is_available"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club
        if club: self.instance.club = club

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.club = self.club
        if commit: obj.save()
        return obj


class CafeOrderForm(forms.ModelForm):
    class Meta:
        model = CafeOrder
        fields = ["branch", "member", "menu_item", "quantity", "notes"]

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        if club: self.instance.club = club
        if club:
            self.fields["branch"].queryset = club.branches.filter(is_active=True)
            self.fields["member"].queryset = club.members.all()
            self.fields["menu_item"].queryset = club.cafe_menu.filter(is_available=True)
