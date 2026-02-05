from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import DailyHealthEntry, DailyScore, Profile
from .services.scoring import compute_overall_score, compute_subscores
from .services.recommendations import generate_advice


@receiver(post_save, sender=DailyHealthEntry)
def create_or_update_daily_score(sender, instance: DailyHealthEntry, created: bool, **kwargs):
    """
    I automatically compute the score after the user submits their daily entry.

    Daily Entry -> hidden subscores -> overall score -> advice -> saved for dashboard/graphs/leaderboard.
    """
    profile, _ = Profile.objects.get_or_create(user=instance.user)

    subscores = compute_subscores(
        calories_kcal=instance.calories_kcal,
        water_ml=instance.water_ml,
        sleep_hours=instance.sleep_hours,
        exercise_minutes=instance.exercise_minutes,
        activity_level=profile.activity_level,
        weight_kg=profile.weight_kg,
    )

    overall = compute_overall_score(subscores)

    advice = generate_advice(
        subscores=subscores,
        raw={
            "calories_kcal": instance.calories_kcal,
            "water_ml": instance.water_ml,
            "sleep_hours": instance.sleep_hours,
            "exercise_minutes": instance.exercise_minutes,
        },
        activity_level=profile.activity_level,
        weight_kg=profile.weight_kg,
    )

    DailyScore.objects.update_or_create(
        user=instance.user,
        date=instance.date,
        defaults={
            "overall_score": overall,
            "subscores": subscores,
            "advice": advice,
        },
    )