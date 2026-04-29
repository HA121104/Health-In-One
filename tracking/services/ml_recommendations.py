from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
from django.conf import settings

from .recommendations import generate_advice
from .scoring import get_specs


ACTIVITY_MAP = {
    "SEDENTARY": 0,
    "LIGHT": 1,
    "MODERATE": 2,
    "ACTIVE": 3,
}

GOAL_MAP = {
    "GENERAL": 0,
    "FITNESS": 1,
    "WEIGHT_LOSS": 2,
    "MUSCLE_GAIN": 3,
    "WELLBEING": 4,
}


def encode_activity(activity_level: str) -> int:
    """
    I encode activity level into a number because the ML model cannot process
    text values directly.
    """
    return ACTIVITY_MAP.get(activity_level, ACTIVITY_MAP["MODERATE"])


def encode_goal(health_goal: str) -> int:
    """
    I encode the health goal into a number so the model can use it as a feature.
    """
    return GOAL_MAP.get(health_goal, GOAL_MAP["GENERAL"])


@lru_cache(maxsize=1)
def load_model_artifact() -> dict:
    """
    I cache the model after loading it once so the app does not reload the
    .joblib file on every request.
    """
    model_path = Path(settings.BASE_DIR) / "tracking" / "ml_artifacts" / "health_score_model.joblib"

    if not model_path.exists():
        raise FileNotFoundError(
            "ML model file not found. Run: python -m tracking.ml.train_model"
        )

    return joblib.load(model_path)


def get_history_average(user, current_date, days: int, fallback_score: int) -> float:
    """
    I calculate previous average scores so the ML model considers history,
    not only today's inputs.

    If the user has no history yet, I use today's score as a fallback so the
    model still receives a sensible value.
    """
    from tracking.models import DailyScore

    scores = (
        DailyScore.objects
        .filter(user=user, date__lt=current_date)
        .order_by("-date")[:days]
    )

    values = [score.overall_score for score in scores]

    if not values:
        return float(fallback_score)

    return sum(values) / len(values)


def build_feature_row(raw: Dict[str, float], profile, avg_7: float, avg_30: float) -> List[float]:
    """
    I build the exact feature order expected by the trained model.

    Keeping this centralised is important because the training data and live
    prediction data must use the same feature order.
    """
    return [
        float(profile.age or 30),
        float(profile.height_cm or 170),
        float(profile.weight_kg or 70),
        float(encode_activity(profile.activity_level)),
        float(encode_goal(profile.health_goal)),
        float(raw["calories_kcal"]),
        float(raw["water_ml"]),
        float(raw["sleep_hours"]),
        float(raw["exercise_minutes"]),
        float(raw["steps"]),
        float(raw["screen_time_hours"]),
        float(raw["stress_level"]),
        float(raw["mood_level"]),
        float(raw["energy_level"]),
        float(raw["fruit_veg_servings"]),
        float(raw["protein_grams"]),
        float(avg_7),
        float(avg_30),
    ]


def predict_score(raw: Dict[str, float], profile, avg_7: float, avg_30: float) -> float:
    """
    I use the ML model to predict the likely health score for a specific set
    of inputs.
    """
    artifact = load_model_artifact()
    model = artifact["model"]

    row = build_feature_row(raw, profile, avg_7, avg_30)
    prediction = model.predict([row])[0]

    return float(prediction)


def midpoint(low: float, high: float) -> float:
    """
    I use the midpoint of an ideal range as a simple target value when testing
    possible improvements.
    """
    return (low + high) / 2


def add_candidate(
    candidates: List[dict],
    *,
    key: str,
    metric_name: str,
    action: str,
    tip: str,
    raw: Dict[str, float],
    updates: Dict[str, float],
) -> None:
    """
    I store each possible improvement as a candidate.

    Later, the ML model predicts the score for each candidate and chooses the
    ones with the biggest improvement.
    """
    candidate_raw = raw.copy()
    candidate_raw.update(updates)

    candidates.append({
        "key": key,
        "metric_name": metric_name,
        "action": action,
        "tip": tip,
        "raw": candidate_raw,
    })


def build_improvement_candidates(raw: Dict[str, float], profile) -> List[dict]:
    """
    I create possible health improvements and let the ML model decide which
    one is predicted to help the most.

    This makes the recommendation process ML-led instead of hard-coded.
    """
    specs = get_specs(
        activity_level=profile.activity_level,
        weight_kg=profile.weight_kg,
        health_goal=profile.health_goal,
    )

    candidates: List[dict] = []

    # Calories
    calories_spec = specs["calories"]
    if raw["calories_kcal"] < calories_spec.ideal_low or raw["calories_kcal"] > calories_spec.ideal_high:
        target = midpoint(calories_spec.ideal_low, calories_spec.ideal_high)
        add_candidate(
            candidates,
            key="calories",
            metric_name="Calories",
            action=f"move calorie intake closer to around {int(target)} kcal",
            tip="Adjust portion sizes or meal planning so intake moves closer to your target range.",
            raw=raw,
            updates={"calories_kcal": target},
        )

    # Water
    water_spec = specs["water"]
    if raw["water_ml"] < water_spec.ideal_low or raw["water_ml"] > water_spec.ideal_high:
        target = midpoint(water_spec.ideal_low, water_spec.ideal_high)
        add_candidate(
            candidates,
            key="water",
            metric_name="Water",
            action=f"move water intake closer to around {int(target)} ml",
            tip="Drink water gradually throughout the day instead of only in large amounts at once.",
            raw=raw,
            updates={"water_ml": target},
        )

    # Sleep
    sleep_spec = specs["sleep"]
    if raw["sleep_hours"] < sleep_spec.ideal_low or raw["sleep_hours"] > sleep_spec.ideal_high:
        target = midpoint(sleep_spec.ideal_low, sleep_spec.ideal_high)
        add_candidate(
            candidates,
            key="sleep",
            metric_name="Sleep",
            action=f"aim for around {target:.1f} hours of sleep",
            tip="Set a consistent bedtime and reduce screens/caffeine late in the evening.",
            raw=raw,
            updates={"sleep_hours": target},
        )

    # Exercise
    exercise_spec = specs["exercise"]
    if raw["exercise_minutes"] < exercise_spec.ideal_low or raw["exercise_minutes"] > exercise_spec.ideal_high:
        target = midpoint(exercise_spec.ideal_low, exercise_spec.ideal_high)
        add_candidate(
            candidates,
            key="exercise",
            metric_name="Exercise",
            action=f"move exercise closer to around {int(target)} minutes",
            tip="A walk, gym session, or short home workout can help build consistency.",
            raw=raw,
            updates={"exercise_minutes": target},
        )

    # Steps
    steps_spec = specs["steps"]
    if raw["steps"] < steps_spec.ideal_low or raw["steps"] > steps_spec.ideal_high:
        target = midpoint(steps_spec.ideal_low, steps_spec.ideal_high)
        add_candidate(
            candidates,
            key="steps",
            metric_name="Steps",
            action=f"move steps closer to around {int(target)} steps",
            tip="Add short walks after meals or between study/work sessions.",
            raw=raw,
            updates={"steps": target},
        )

    # Screen time
    screen_spec = specs["screen_time"]
    if raw["screen_time_hours"] > screen_spec.ideal_high:
        add_candidate(
            candidates,
            key="screen_time",
            metric_name="Screen time",
            action="reduce screen time closer to 5–6 hours",
            tip="Try replacing one screen-heavy period with a walk, gym session, or offline break.",
            raw=raw,
            updates={"screen_time_hours": 5},
        )

    # Stress
    stress_spec = specs["stress"]
    if raw["stress_level"] > stress_spec.ideal_high:
        add_candidate(
            candidates,
            key="stress",
            metric_name="Stress",
            action="reduce stress closer to a low-to-moderate level",
            tip="Use a short break, breathing routine, journalling, or light exercise to reduce stress.",
            raw=raw,
            updates={"stress_level": 3},
        )

    # Mood
    mood_spec = specs["mood"]
    if raw["mood_level"] < mood_spec.ideal_low:
        add_candidate(
            candidates,
            key="mood",
            metric_name="Mood",
            action="improve mood level towards 7 or above",
            tip="Do one enjoyable activity, speak to someone, or take a short outdoor break.",
            raw=raw,
            updates={"mood_level": 7},
        )

    # Energy
    energy_spec = specs["energy"]
    if raw["energy_level"] < energy_spec.ideal_low:
        add_candidate(
            candidates,
            key="energy",
            metric_name="Energy",
            action="improve energy level towards 7 or above",
            tip="Check sleep, hydration and food timing because these strongly affect energy.",
            raw=raw,
            updates={"energy_level": 7},
        )

    # Fruit and vegetables
    fruit_spec = specs["fruit_veg"]
    if raw["fruit_veg_servings"] < fruit_spec.ideal_low:
        add_candidate(
            candidates,
            key="fruit_veg",
            metric_name="Fruit and vegetables",
            action="increase fruit/vegetable intake to around 5 servings",
            tip="Add fruit at breakfast or vegetables to lunch/dinner to raise this consistently.",
            raw=raw,
            updates={"fruit_veg_servings": 5},
        )

    # Protein
    protein_spec = specs["protein"]
    if raw["protein_grams"] < protein_spec.ideal_low or raw["protein_grams"] > protein_spec.ideal_high:
        target = midpoint(protein_spec.ideal_low, protein_spec.ideal_high)
        add_candidate(
            candidates,
            key="protein",
            metric_name="Protein",
            action=f"move protein intake closer to around {int(target)} g",
            tip="Use lean protein sources such as eggs, chicken, fish, yoghurt, beans or tofu.",
            raw=raw,
            updates={"protein_grams": target},
        )

    return candidates


def generate_ml_recommendations(
    *,
    entry,
    profile,
    subscores: Dict[str, int],
    current_overall_score: int,
) -> Tuple[List[str], Dict[str, dict], str]:
    """
    I generate ML-led recommendations by comparing predicted scores.

    The process is:
    1. Predict the score for the user's current data.
    2. Create possible improvement scenarios.
    3. Predict the score for each scenario.
    4. Recommend the changes with the largest predicted improvement.

    This makes ML the main decision-maker for advice.
    """
    raw = {
        "calories_kcal": float(entry.calories_kcal),
        "water_ml": float(entry.water_ml),
        "sleep_hours": float(entry.sleep_hours),
        "exercise_minutes": float(entry.exercise_minutes),
        "steps": float(entry.steps),
        "screen_time_hours": float(entry.screen_time_hours),
        "stress_level": float(entry.stress_level),
        "mood_level": float(entry.mood_level),
        "energy_level": float(entry.energy_level),
        "fruit_veg_servings": float(entry.fruit_veg_servings),
        "protein_grams": float(entry.protein_grams),
    }

    try:
        artifact = load_model_artifact()
        model_version = artifact.get("model_version", "ml_model")

        avg_7 = get_history_average(entry.user, entry.date, 7, current_overall_score)
        avg_30 = get_history_average(entry.user, entry.date, 30, current_overall_score)

        current_prediction = predict_score(raw, profile, avg_7, avg_30)
        candidates = build_improvement_candidates(raw, profile)

        predicted_improvements: Dict[str, dict] = {}

        for candidate in candidates:
            predicted_score = predict_score(candidate["raw"], profile, avg_7, avg_30)
            gain = predicted_score - current_prediction

            predicted_improvements[candidate["key"]] = {
                "metric": candidate["metric_name"],
                "action": candidate["action"],
                "tip": candidate["tip"],
                "current_predicted_score": round(current_prediction, 2),
                "predicted_score_after_change": round(predicted_score, 2),
                "predicted_gain": round(gain, 2),
            }

        ranked = sorted(
            predicted_improvements.values(),
            key=lambda item: item["predicted_gain"],
            reverse=True,
        )

        useful = [item for item in ranked if item["predicted_gain"] > 0.5]

        if not useful:
            advice = [
                "Top focus today: maintain consistency. The ML model did not identify a major single change likely to improve your score significantly.",
                "ML recommendation: Your current metrics are already fairly balanced compared with your recent pattern.",
                "Tip: Keep logging daily so the model has more history to personalise future recommendations.",
            ]
        else:
            top = useful[:3]
            top_names = ", ".join(item["metric"] for item in top)

            advice = [
                f"Top focus today: {top_names}. These are the changes the ML model predicts will improve your score the most.",
            ]

            for item in top:
                advice.append(
                    f"ML recommendation: {item['metric']} — {item['action']}. "
                    f"This is predicted to improve your score by about {item['predicted_gain']} points."
                )
                advice.append(f"Tip: {item['tip']}")

        return advice, predicted_improvements, model_version

    except Exception:
        # I keep this fallback so the app still works even if the model file is missing
        # during development or deployment.
        fallback_advice = generate_advice(
            subscores=subscores,
            raw={
                "calories_kcal": entry.calories_kcal,
                "water_ml": entry.water_ml,
                "sleep_hours": entry.sleep_hours,
                "exercise_minutes": entry.exercise_minutes,
                "steps": entry.steps,
                "screen_time_hours": entry.screen_time_hours,
                "stress_level": entry.stress_level,
                "mood_level": entry.mood_level,
                "energy_level": entry.energy_level,
                "fruit_veg_servings": entry.fruit_veg_servings,
                "protein_grams": entry.protein_grams,
            },
            activity_level=profile.activity_level,
            weight_kg=profile.weight_kg,
        )

        return fallback_advice, {}, "rule_based_fallback"