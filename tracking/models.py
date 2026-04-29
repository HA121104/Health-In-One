from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Profile(models.Model):
    """
    I store user profile information because the scoring and ML recommendation model
    need context about the user, not just their daily metrics.
    """

    class ActivityLevel(models.TextChoices):
        SEDENTARY = "SEDENTARY", "Sedentary"
        LIGHT = "LIGHT", "Light"
        MODERATE = "MODERATE", "Moderate"
        ACTIVE = "ACTIVE", "Active"

    class HealthGoal(models.TextChoices):
        GENERAL = "GENERAL", "General health"
        FITNESS = "FITNESS", "Improve fitness"
        WEIGHT_LOSS = "WEIGHT_LOSS", "Weight loss"
        MUSCLE_GAIN = "MUSCLE_GAIN", "Muscle gain"
        WELLBEING = "WELLBEING", "Improve wellbeing"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # I added age and height because the final ML model needs richer user profile features.
    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(13), MaxValueValidator(100)],
    )

    height_cm = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(100), MaxValueValidator(230)],
    )

    weight_kg = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)],
    )

    activity_level = models.CharField(
        max_length=20,
        choices=ActivityLevel.choices,
        default=ActivityLevel.MODERATE,
    )

    health_goal = models.CharField(
        max_length=20,
        choices=HealthGoal.choices,
        default=HealthGoal.GENERAL,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class DailyHealthEntry(models.Model):
    """
    This model stores the raw health data entered by the user each day.

    I expanded it for the final version so the ML model has more meaningful features
    than just water, sleep, exercise and calories.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_entries")
    date = models.DateField(default=timezone.localdate)

    # Original core metrics
    calories_kcal = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(8000)]
    )

    water_ml = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(8000)]
    )

    sleep_hours = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(16)]
    )

    exercise_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(300)]
    )

    # New final-version metrics
    steps = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(60000)],
    )

    screen_time_hours = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )

    stress_level = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    mood_level = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    energy_level = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    fruit_veg_servings = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(15)],
    )

    protein_grams = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(350)],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class DailyScore(models.Model):
    """
    This model stores the processed results for a user's daily entry.

    The overall score is visible to the user.
    The subscores and ML prediction details are stored internally so they can support
    recommendations, charts, history and final report evidence.
    """

    class RecommendationSource(models.TextChoices):
        RULE_BASED = "RULE_BASED", "Rule-based"
        ML_MODEL = "ML_MODEL", "Machine learning"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_scores")
    date = models.DateField()

    overall_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # I store hidden per-metric scores here because the user sees the overall score,
    # while the system uses the subscores for recommendations and ML features.
    subscores = models.JSONField(default=dict)

    # The advice shown to the user.
    advice = models.JSONField(default=list)

    # These fields are added for the final ML version.
    recommendation_source = models.CharField(
        max_length=20,
        choices=RecommendationSource.choices,
        default=RecommendationSource.RULE_BASED,
    )

    predicted_improvements = models.JSONField(
        default=dict,
        blank=True,
    )

    model_version = models.CharField(
        max_length=50,
        default="rule_based_baseline",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.overall_score}"