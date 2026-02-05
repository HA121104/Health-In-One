from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, DailyHealthEntry


class SignUpForm(UserCreationForm):
    """
    I use Django’s built-in UserCreationForm because it’s secure and saves time.
    """
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ProfileForm(forms.ModelForm):
    """
    I keep profile editing minimal for the interim MVP.
    """
    class Meta:
        model = Profile
        fields = ("weight_kg", "activity_level")


class DailyHealthEntryForm(forms.ModelForm):
    """
    This is the daily input form users fill in.
    Once saved, my signal automatically creates/updates the DailyScore.
    """
    class Meta:
        model = DailyHealthEntry
        fields = ("date", "calories_kcal", "water_ml", "sleep_hours", "exercise_minutes")

        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }