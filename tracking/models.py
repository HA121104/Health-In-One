from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    """
    I store a lightweight profile because my scoring targets can depend on the user.
    """

    class ActivityLevel(models.TextChoices):
        SEDENTARY = "SEDENTARY", "Sedentary"
        LIGHT = "LIGHT", "Light"
        MODERATE = "MODERATE", "Moderate"
        ACTIVE = "ACTIVE", "Active"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # I use positive fields so negatives are impossible at the database level.
    weight_kg = models.PositiveIntegerField(null=True, blank=True)

    activity_level = models.CharField(
        max_length=20,
        choices=ActivityLevel.choices,
        default=ActivityLevel.MODERATE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DailyHealthEntry(models.Model):
    """
    Raw metrics entered by the user each day.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_entries")
    date = models.DateField(default=timezone.localdate)

    calories_kcal = models.PositiveIntegerField()
    water_ml = models.PositiveIntegerField()
    sleep_hours = models.PositiveIntegerField()
    exercise_minutes = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date")


class DailyScore(models.Model):
    """
    Stores the calculated overall score plus hidden subscores and advice.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_scores")
    date = models.DateField()

    overall_score = models.PositiveIntegerField()
    subscores = models.JSONField()
    advice = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date")
       