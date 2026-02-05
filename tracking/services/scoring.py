from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class RangeSpec:
    """
    I use RangeSpec to define:
    - the ideal range (low/high)
    - how harshly I penalise values below vs above the ideal range (tolerances)

    This lets me score BOTH "too low" and "too high" inputs (because both can be harmful).
    """
    ideal_low: float
    ideal_high: float
    tolerance_low: float
    tolerance_high: float


def clamp_score(x: float) -> int:
    """
    I clamp to a clean integer 0–100 because:
    - it’s easy to show on dashboards/leaderboards
    - it matches the project requirement of a 0–100 score
    """
    if x < 0:
        return 0
    if x > 100:
        return 100
    return int(round(x))


def score_from_range(value: float, spec: RangeSpec) -> int:
    """
    I convert a raw input into a 0–100 score based on distance from an ideal range.

    - In range => 100
    - Below => decreases linearly until it hits 0 at tolerance_low
    - Above => decreases linearly until it hits 0 at tolerance_high

    I picked this because it is:
    - simple to explain in the report/viva
    - deterministic (always gives the same result)
    - easy to tune later (just change the range/tolerances)
    """
    if spec.ideal_low <= value <= spec.ideal_high:
        return 100

    if value < spec.ideal_low:
        distance = spec.ideal_low - value
        raw = 100 * (1 - (distance / spec.tolerance_low))
        return clamp_score(raw)

    distance = value - spec.ideal_high
    raw = 100 * (1 - (distance / spec.tolerance_high))
    return clamp_score(raw)


def get_specs(activity_level: str, weight_kg: float | None) -> Dict[str, RangeSpec]:
    """
    I centralise all scoring ranges here so I can tweak them quickly.

    For interim MVP I keep ranges realistic and simple:
    - Water: ideal 2000–3000ml
    - Sleep: ideal 7–9 hours
    - Exercise: depends on activity level
    - Calories: rough target based on weight (if present), otherwise generic range

    Note: The goal is NOT medical accuracy. The goal is consistent scoring + useful feedback.
    """
    # Water: low is common and harmful; high only becomes an issue at extremes,
    # so I allow a larger tolerance on the high side.
    water = RangeSpec(ideal_low=2000, ideal_high=3000, tolerance_low=2000, tolerance_high=3000)

    # Sleep: both too low and too high can be undesirable.
    sleep = RangeSpec(ideal_low=7, ideal_high=9, tolerance_low=5, tolerance_high=4)

    # Exercise: personalised by activity level (simple but effective).
    exercise_map = {
        "SEDENTARY": RangeSpec(ideal_low=15, ideal_high=40, tolerance_low=15, tolerance_high=120),
        "LIGHT": RangeSpec(ideal_low=20, ideal_high=45, tolerance_low=20, tolerance_high=120),
        "MODERATE": RangeSpec(ideal_low=30, ideal_high=60, tolerance_low=30, tolerance_high=120),
        "ACTIVE": RangeSpec(ideal_low=40, ideal_high=75, tolerance_low=40, tolerance_high=120),
    }
    exercise = exercise_map.get(activity_level, exercise_map["MODERATE"])

    # Calories: for interim I estimate a target from weight if available.
    # If weight is missing, I fall back to a generic healthy-ish range.
    if weight_kg and weight_kg > 0:
        target = weight_kg * 30  # simple rule-of-thumb for daily energy needs
        calories = RangeSpec(
            ideal_low=target - 300,
            ideal_high=target + 300,
            tolerance_low=1200,   # how far below before score ~0
            tolerance_high=900,   # harsher penalty for too high (detrimental overeating)
        )
    else:
        calories = RangeSpec(ideal_low=1800, ideal_high=2500, tolerance_low=1200, tolerance_high=1200)

    return {"water": water, "sleep": sleep, "exercise": exercise, "calories": calories}


def compute_subscores(
    *,
    calories_kcal: int,
    water_ml: int,
    sleep_hours: float,
    exercise_minutes: int,
    activity_level: str,
    weight_kg: float | None,
) -> Dict[str, int]:
    """
    I compute each metric score independently so:
    - I can explain each metric in isolation
    - I can generate targeted recommendations based on the weakest metric(s)
    - I can hide subscores from the user but still use them internally
    """
    specs = get_specs(activity_level=activity_level, weight_kg=weight_kg)

    subscores = {
        "water": score_from_range(water_ml, specs["water"]),
        "sleep": score_from_range(sleep_hours, specs["sleep"]),
        "exercise": score_from_range(exercise_minutes, specs["exercise"]),
        "calories": score_from_range(calories_kcal, specs["calories"]),
    }
    return subscores


def compute_overall_score(subscores: Dict[str, int]) -> int:
    """
    I average the subscores to get the daily overall score.

    For the interim MVP I keep weights equal because:
    - it’s simple and transparent
    - it avoids arguing about which metric “matters more”
    """
    if not subscores:
        return 0
    return clamp_score(sum(subscores.values()) / len(subscores))