from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import DailyHealthEntry, DailyScore, Profile
from .services.ml_recommendations import generate_ml_recommendations
from .services.scoring import compute_overall_score, compute_subscores


@receiver(post_save, sender=DailyHealthEntry)
def create_or_update_daily_score(sender, instance: DailyHealthEntry, created: bool, **kwargs):
    """
    I automatically calculate a DailyScore whenever a user saves a DailyHealthEntry.

    I use a Django signal because the view should only be responsible for saving
    raw user input. The scoring and ML recommendation pipeline should run
    automatically in the background.
    """
    profile, _ = Profile.objects.get_or_create(user=instance.user)

    subscores = compute_subscores(
        calories_kcal=instance.calories_kcal,
        water_ml=instance.water_ml,
        sleep_hours=instance.sleep_hours,
        exercise_minutes=instance.exercise_minutes,
        steps=instance.steps,
        screen_time_hours=instance.screen_time_hours,
        stress_level=instance.stress_level,
        mood_level=instance.mood_level,
        energy_level=instance.energy_level,
        fruit_veg_servings=instance.fruit_veg_servings,
        protein_grams=instance.protein_grams,
        activity_level=profile.activity_level,
        weight_kg=profile.weight_kg,
        health_goal=profile.health_goal,
    )

    overall = compute_overall_score(subscores)

    advice, predicted_improvements, model_version = generate_ml_recommendations(
        entry=instance,
        profile=profile,
        subscores=subscores,
        current_overall_score=overall,
    )

    if model_version.startswith("ml_"):
        recommendation_source = DailyScore.RecommendationSource.ML_MODEL
    else:
        recommendation_source = DailyScore.RecommendationSource.RULE_BASED

    DailyScore.objects.update_or_create(
        user=instance.user,
        date=instance.date,
        defaults={
            "overall_score": overall,
            "subscores": subscores,
            "advice": advice,
            "recommendation_source": recommendation_source,
            "predicted_improvements": predicted_improvements,
            "model_version": model_version,
        },
    )