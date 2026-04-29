from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RangeSpec:
    """
    I use this class to keep every scoring range organised in one format.

    Each metric has:
    - an ideal low value
    - an ideal high value
    - a tolerance below the ideal range
    - a tolerance above the ideal range

    I did this because it lets me score values that are too low and too high
    without writing separate logic for every single metric.
    """
    ideal_low: float
    ideal_high: float
    tolerance_low: float
    tolerance_high: float


# I give each metric a weight so the overall score is not just a simple average.
# I weighted sleep, calories, exercise and stress slightly higher because they are
# important overall lifestyle indicators in this project.
METRIC_WEIGHTS = {
    "calories": 0.12,
    "water": 0.10,
    "sleep": 0.14,
    "exercise": 0.12,
    "steps": 0.10,
    "screen_time": 0.08,
    "stress": 0.10,
    "mood": 0.08,
    "energy": 0.06,
    "fruit_veg": 0.05,
    "protein": 0.05,
}


def clamp_score(value: float) -> int:
    """
    I clamp scores between 0 and 100 because the project uses a clear 0–100
    health scoring system.
    """
    if value < 0:
        return 0
    if value > 100:
        return 100
    return int(round(value))


def score_from_range(value: float, spec: RangeSpec) -> int:
    """
    I score a raw value based on how close it is to an ideal range.

    - If the value is inside the ideal range, it gets 100.
    - If it is below the range, the score drops based on how far below it is.
    - If it is above the range, the score drops based on how far above it is.

    I chose this method because it is easy to explain in the report and it also
    handles harmful extremes, such as too much screen time or extreme exercise.
    """
    if spec.ideal_low <= value <= spec.ideal_high:
        return 100

    if value < spec.ideal_low:
        distance = spec.ideal_low - value
        tolerance = max(spec.tolerance_low, 0.0001)
        return clamp_score(100 * (1 - distance / tolerance))

    distance = value - spec.ideal_high
    tolerance = max(spec.tolerance_high, 0.0001)
    return clamp_score(100 * (1 - distance / tolerance))


def get_calorie_target(weight_kg: float | None, health_goal: str) -> float:
    """
    I calculate a simple calorie target from body weight and health goal.

    I am not trying to create a medical calorie calculator here.
    I am using a consistent project-level estimate so the app can personalise
    scoring in a meaningful way.
    """
    if weight_kg and weight_kg > 0:
        target = weight_kg * 30
    else:
        target = 2200

    if health_goal == "WEIGHT_LOSS":
        target -= 300
    elif health_goal == "MUSCLE_GAIN":
        target += 300
    elif health_goal == "FITNESS":
        target += 100

    return max(target, 1200)


def get_specs(activity_level: str, weight_kg: float | None, health_goal: str = "GENERAL") -> Dict[str, RangeSpec]:
    """
    I keep all ideal ranges in one function so the scoring system is easy to
    maintain, tune and explain in the final report.

    These ranges are project assumptions rather than medical diagnosis rules.
    The aim is to produce consistent health behaviour scoring for the prototype.
    """

    # Water: too little is common, but too much can also be unbalanced.
    water = RangeSpec(
        ideal_low=2000,
        ideal_high=3000,
        tolerance_low=2000,
        tolerance_high=3000,
    )

    # Sleep: 7–9 hours is treated as the ideal range for this project.
    sleep = RangeSpec(
        ideal_low=7,
        ideal_high=9,
        tolerance_low=5,
        tolerance_high=4,
    )

    # Exercise and steps are adjusted by activity level so the scoring is more personalised.
    exercise_map = {
        "SEDENTARY": RangeSpec(ideal_low=15, ideal_high=40, tolerance_low=15, tolerance_high=120),
        "LIGHT": RangeSpec(ideal_low=20, ideal_high=45, tolerance_low=20, tolerance_high=120),
        "MODERATE": RangeSpec(ideal_low=30, ideal_high=60, tolerance_low=30, tolerance_high=120),
        "ACTIVE": RangeSpec(ideal_low=40, ideal_high=75, tolerance_low=40, tolerance_high=120),
    }

    steps_map = {
        "SEDENTARY": RangeSpec(ideal_low=4000, ideal_high=8000, tolerance_low=4000, tolerance_high=15000),
        "LIGHT": RangeSpec(ideal_low=6000, ideal_high=10000, tolerance_low=6000, tolerance_high=15000),
        "MODERATE": RangeSpec(ideal_low=8000, ideal_high=12000, tolerance_low=8000, tolerance_high=18000),
        "ACTIVE": RangeSpec(ideal_low=10000, ideal_high=16000, tolerance_low=10000, tolerance_high=20000),
    }

    exercise = exercise_map.get(activity_level, exercise_map["MODERATE"])
    steps = steps_map.get(activity_level, steps_map["MODERATE"])

    calorie_target = get_calorie_target(weight_kg, health_goal)
    calories = RangeSpec(
        ideal_low=calorie_target - 300,
        ideal_high=calorie_target + 300,
        tolerance_low=1200,
        tolerance_high=1000,
    )

    # Screen time: lower is generally better, but I allow a realistic ideal range.
    screen_time = RangeSpec(
        ideal_low=0,
        ideal_high=6,
        tolerance_low=1,
        tolerance_high=10,
    )

    # Stress: lower is better, so 1–4 is treated as ideal.
    stress = RangeSpec(
        ideal_low=1,
        ideal_high=4,
        tolerance_low=1,
        tolerance_high=6,
    )

    # Mood and energy: higher is better, so 7–10 is ideal.
    mood = RangeSpec(
        ideal_low=7,
        ideal_high=10,
        tolerance_low=6,
        tolerance_high=1,
    )

    energy = RangeSpec(
        ideal_low=7,
        ideal_high=10,
        tolerance_low=6,
        tolerance_high=1,
    )

    # Fruit/veg: 5+ servings is treated as the ideal range.
    fruit_veg = RangeSpec(
        ideal_low=5,
        ideal_high=10,
        tolerance_low=5,
        tolerance_high=5,
    )

    # Protein: personalised using weight where available.
    if weight_kg and weight_kg > 0:
        protein_target = weight_kg * 1.2
        protein = RangeSpec(
            ideal_low=protein_target * 0.8,
            ideal_high=protein_target * 1.4,
            tolerance_low=protein_target * 0.8,
            tolerance_high=150,
        )
    else:
        protein = RangeSpec(
            ideal_low=60,
            ideal_high=130,
            tolerance_low=60,
            tolerance_high=150,
        )

    return {
        "calories": calories,
        "water": water,
        "sleep": sleep,
        "exercise": exercise,
        "steps": steps,
        "screen_time": screen_time,
        "stress": stress,
        "mood": mood,
        "energy": energy,
        "fruit_veg": fruit_veg,
        "protein": protein,
    }


def compute_subscores(
    *,
    calories_kcal: int,
    water_ml: int,
    sleep_hours: float,
    exercise_minutes: int,
    steps: int,
    screen_time_hours: float,
    stress_level: int,
    mood_level: int,
    energy_level: int,
    fruit_veg_servings: int,
    protein_grams: int,
    activity_level: str,
    weight_kg: float | None,
    health_goal: str = "GENERAL",
) -> Dict[str, int]:
    """
    I convert every raw daily input into a hidden subscore out of 100.

    The user only sees the overall score, but these subscores are important
    because they will become the feature inputs for the final ML recommendation model.
    """
    specs = get_specs(
        activity_level=activity_level,
        weight_kg=weight_kg,
        health_goal=health_goal,
    )

    return {
        "calories": score_from_range(calories_kcal, specs["calories"]),
        "water": score_from_range(water_ml, specs["water"]),
        "sleep": score_from_range(sleep_hours, specs["sleep"]),
        "exercise": score_from_range(exercise_minutes, specs["exercise"]),
        "steps": score_from_range(steps, specs["steps"]),
        "screen_time": score_from_range(screen_time_hours, specs["screen_time"]),
        "stress": score_from_range(stress_level, specs["stress"]),
        "mood": score_from_range(mood_level, specs["mood"]),
        "energy": score_from_range(energy_level, specs["energy"]),
        "fruit_veg": score_from_range(fruit_veg_servings, specs["fruit_veg"]),
        "protein": score_from_range(protein_grams, specs["protein"]),
    }


def compute_overall_score(subscores: Dict[str, int]) -> int:
    """
    I calculate a weighted overall score from the hidden subscores.

    I use a weighted score instead of a basic average because the final project
    tracks more metrics, and some should influence the overall result more than others.
    """
    if not subscores:
        return 0

    total = 0.0
    total_weight = 0.0

    for metric, score in subscores.items():
        weight = METRIC_WEIGHTS.get(metric, 0)
        total += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0

    return clamp_score(total / total_weight)