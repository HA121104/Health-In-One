from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, DailyHealthEntry


class SignUpForm(UserCreationForm):
    """
    I use Django's built-in UserCreationForm because it handles secure password
    validation and avoids me manually managing password hashing.
    """

    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ProfileForm(forms.ModelForm):
    """
    I use controlled fields for the profile so users cannot enter unrealistic
    values and so the ML model has reliable profile data to work with.
    """

    class Meta:
        model = Profile
        fields = ("age", "height_cm", "weight_kg", "activity_level", "health_goal")

        widgets = {
            "age": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "13",
                "max": "100",
                "placeholder": "e.g. 22",
            }),
            "height_cm": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "100",
                "max": "230",
                "placeholder": "e.g. 175",
            }),
            "weight_kg": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "30",
                "max": "250",
                "step": "0.1",
                "placeholder": "e.g. 70.5",
            }),
            "activity_level": forms.Select(attrs={
                "class": "form-select",
            }),
            "health_goal": forms.Select(attrs={
                "class": "form-select",
            }),
        }


class DailyHealthEntryForm(forms.ModelForm):
    """
    I removed the date field from the public form because final users should only
    log today's metrics.

    I still keep the date in the model, but the view sets it automatically.
    This prevents users from creating future entries or changing older results
    through the normal UI.
    """

    class Meta:
        model = DailyHealthEntry

        # I deliberately exclude "date" because the view will set it to today's date.
        fields = (
            "calories_kcal",
            "water_ml",
            "sleep_hours",
            "exercise_minutes",
            "steps",
            "screen_time_hours",
            "stress_level",
            "mood_level",
            "energy_level",
            "fruit_veg_servings",
            "protein_grams",
        )

        widgets = {
            "calories_kcal": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "0",
                "max": "8000",
                "step": "50",
            }),
            "water_ml": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "0",
                "max": "8000",
                "step": "100",
            }),
            "sleep_hours": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "0",
                "max": "16",
                "step": "0.5",
            }),
            "exercise_minutes": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "0",
                "max": "300",
                "step": "5",
            }),
            "steps": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "0",
                "max": "60000",
                "step": "500",
            }),
            "screen_time_hours": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "0",
                "max": "24",
                "step": "0.5",
            }),
            "stress_level": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "1",
                "max": "10",
                "step": "1",
            }),
            "mood_level": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "1",
                "max": "10",
                "step": "1",
            }),
            "energy_level": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "1",
                "max": "10",
                "step": "1",
            }),
            "fruit_veg_servings": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "0",
                "max": "15",
                "step": "1",
            }),
            "protein_grams": forms.NumberInput(attrs={
                "class": "form-range metric-slider",
                "type": "range",
                "min": "0",
                "max": "350",
                "step": "5",
            }),
        }

        labels = {
            "calories_kcal": "Calories consumed (kcal)",
            "water_ml": "Water intake (ml)",
            "sleep_hours": "Sleep duration (hours)",
            "exercise_minutes": "Exercise duration (minutes)",
            "steps": "Steps walked",
            "screen_time_hours": "Screen time (hours)",
            "stress_level": "Stress level (1 = low, 10 = high)",
            "mood_level": "Mood level (1 = low, 10 = high)",
            "energy_level": "Energy level (1 = low, 10 = high)",
            "fruit_veg_servings": "Fruit/vegetable servings",
            "protein_grams": "Protein intake (grams)",
        }