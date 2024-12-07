from django import forms
from .models import NotificationSettings

class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = NotificationSettings
        fields = ['is_enabled', 'interval_minutes']
