from django.contrib import admin
from .models import Profile, DailyHealthEntry, DailyScore


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "height_cm", "weight_kg", "activity_level", "health_goal")
    search_fields = ("user__username",)


@admin.register(DailyHealthEntry)
class DailyHealthEntryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date",
        "calories_kcal",
        "water_ml",
        "sleep_hours",
        "exercise_minutes",
        "steps",
        "stress_level",
        "mood_level",
        "energy_level",
    )
    list_filter = ("date", "stress_level", "mood_level", "energy_level")
    search_fields = ("user__username",)


@admin.register(DailyScore)
class DailyScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "overall_score", "recommendation_source", "model_version")
    list_filter = ("recommendation_source", "date")
    search_fields = ("user__username",)