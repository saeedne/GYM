from django import forms
from .models import Lead, LeadActivity, MessageQueue

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["first_name", "last_name", "mobile", "email", "source", "stage", "notes"]

class ActivityForm(forms.ModelForm):
    class Meta:
        model = LeadActivity
        fields = ["activity_type", "summary", "due_at"]
        widgets = {"due_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

class MessageForm(forms.ModelForm):
    class Meta:
        model = MessageQueue
        fields = ["channel", "recipient", "body"]
