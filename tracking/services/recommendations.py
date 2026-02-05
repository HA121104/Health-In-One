from __future__ import annotations

from typing import Dict, List, Tuple

from .scoring import get_specs


def direction(value: float, ideal_low: float, ideal_high: float) -> str:
    # I detect whether the raw value is below / within / above the ideal range.
    if value < ideal_low:
        return "below"
    if value > ideal_high:
        return "above"
    return "within"


def distance_from_range(value: float, ideal_low: float, ideal_high: float) -> float:
    # I measure how far the user is from the closest point in the ideal range.
    if value < ideal_low:
        return ideal_low - value
    if value > ideal_high:
        return value - ideal_high
    return 0.0


def severity(distance: float, step_small: float, step_medium: float, step_large: float) -> str:
    """
    I classify how 'bad' the deviation is.
    I use metric-specific step thresholds so advice feels realistic per metric.
    """
    if distance == 0:
        return "none"
    if distance <= step_small:
        return "small"
    if distance <= step_medium:
        return "medium"
    if distance <= step_large:
        return "large"
    return "extreme"


def generate_advice(
    subscores: Dict[str, int],
    raw: Dict[str, float | int],
    *,
    activity_level: str = "MODERATE",
    weight_kg: float | None = None,
) -> List[str]:
    """
    This is my interim recommendation engine (rule-based).
    I intentionally make it:
    - specific (uses the user's exact amount and ideal ranges)
    - actionable (gives multiple tips)
    - consistent (same logic across metrics)
    """
    specs = get_specs(activity_level=activity_level, weight_kg=weight_kg)
    messages: List[str] = []

    # -------------------
    # WATER
    # -------------------
    water_ml = float(raw.get("water_ml", 0))
    w_spec = specs["water"]
    w_dir = direction(water_ml, w_spec.ideal_low, w_spec.ideal_high)
    w_dist = distance_from_range(water_ml, w_spec.ideal_low, w_spec.ideal_high)
    w_sev = severity(w_dist, step_small=250, step_medium=750, step_large=1500)

    if w_dir == "within":
        messages.append(f"Water is in the ideal range ({int(water_ml)} ml). Keep it consistent.")
    elif w_dir == "below":
        gap_to_low = int(w_spec.ideal_low - water_ml)
        messages.append(
            f"Water is low ({int(water_ml)} ml). You’re about ~{gap_to_low} ml below the ideal minimum ({int(w_spec.ideal_low)}–{int(w_spec.ideal_high)} ml)."
        )
        if w_sev in ("large", "extreme"):
            messages.append("Aim to increase water by 500–1000 ml today (spread across the day).")
        elif w_sev == "medium":
            messages.append("Aim to increase water by ~500 ml today.")
        else:
            messages.append("Aim to increase water by ~250 ml today.")
        messages.append("Tip: drink a glass after waking up and one with each meal.")
        messages.append("Tip: keep a bottle nearby so sipping is automatic.")
    else:  # above
        excess = int(water_ml - w_spec.ideal_high)
        messages.append(
            f"Water is high ({int(water_ml)} ml). You’re about ~{excess} ml above the ideal maximum ({int(w_spec.ideal_low)}–{int(w_spec.ideal_high)} ml)."
        )
        if w_sev in ("large", "extreme"):
            messages.append("Reduce intake gradually and avoid drinking huge amounts quickly.")
        else:
            messages.append("You can reduce water slightly and keep it closer to the ideal range.")
        messages.append("Tip: sip steadily instead of chugging large amounts at once.")

    # -------------------
    # SLEEP
    # -------------------
    sleep_h = float(raw.get("sleep_hours", 0))
    s_spec = specs["sleep"]
    s_dir = direction(sleep_h, s_spec.ideal_low, s_spec.ideal_high)
    s_dist = distance_from_range(sleep_h, s_spec.ideal_low, s_spec.ideal_high)
    s_sev = severity(s_dist, step_small=0.5, step_medium=1.5, step_large=3.0)

    if s_dir == "within":
        messages.append(f"Sleep is in the ideal range ({sleep_h:g} hours). Nice.")
    elif s_dir == "below":
        gap = s_spec.ideal_low - sleep_h
        messages.append(
            f"Sleep is low ({sleep_h:g} hours). You’re about ~{gap:g} hours below the ideal minimum (7–9 hours)."
        )
        if s_sev in ("large", "extreme"):
            messages.append("Aim to add 1–2 hours tonight if possible (recovery will improve your score).")
        elif s_sev == "medium":
            messages.append("Aim to add ~1 hour tonight.")
        else:
            messages.append("Aim to add ~30 minutes tonight.")
        messages.append("Tip: set a fixed bedtime alarm (not just a wake-up alarm).")
        messages.append("Tip: reduce screens/caffeine late evening to fall asleep quicker.")
    else:  # above
        excess = sleep_h - s_spec.ideal_high
        messages.append(
            f"Sleep is high ({sleep_h:g} hours). You’re about ~{excess:g} hours above the ideal maximum (7–9 hours)."
        )
        messages.append("Try keeping sleep closer to 7–9 hours for consistency.")
        messages.append("Tip: if you feel tired despite long sleep, check sleep quality (consistent bed/wake times).")

    # -------------------
    # EXERCISE
    # -------------------
    ex_min = float(raw.get("exercise_minutes", 0))
    e_spec = specs["exercise"]
    e_dir = direction(ex_min, e_spec.ideal_low, e_spec.ideal_high)
    e_dist = distance_from_range(ex_min, e_spec.ideal_low, e_spec.ideal_high)
    e_sev = severity(e_dist, step_small=10, step_medium=25, step_large=60)

    if e_dir == "within":
        messages.append(
            f"Exercise is in your ideal range ({int(ex_min)} mins). Great consistency for your activity level."
        )
    elif e_dir == "below":
        gap = int(e_spec.ideal_low - ex_min)
        messages.append(
            f"Exercise is low ({int(ex_min)} mins). You’re about ~{gap} mins below your ideal minimum ({int(e_spec.ideal_low)}–{int(e_spec.ideal_high)} mins)."
        )
        if e_sev in ("large", "extreme"):
            messages.append("Add a short session today: 20–30 mins walk, bike, or a simple home workout.")
        elif e_sev == "medium":
            messages.append("Try adding 10–20 mins of activity today.")
        else:
            messages.append("Try adding 10 mins of activity today.")
        messages.append("Tip: make it easy—walk after lunch/dinner or do a 10-min YouTube routine.")
        messages.append("Tip: consistency beats intensity for improving your weekly average score.")
    else:  # above
        excess = int(ex_min - e_spec.ideal_high)
        messages.append(
            f"Exercise is high ({int(ex_min)} mins). You’re about ~{excess} mins above your ideal maximum ({int(e_spec.ideal_low)}–{int(e_spec.ideal_high)} mins)."
        )
        if e_sev in ("large", "extreme"):
            messages.append("Consider rest/recovery to avoid overtraining. A lighter day can improve overall balance.")
        else:
            messages.append("You can reduce exercise slightly or include a rest day to stay balanced.")
        messages.append("Tip: prioritise sleep and hydration on high-activity days.")

    # -------------------
    # CALORIES
    # -------------------
    kcal = float(raw.get("calories_kcal", 0))
    c_spec = specs["calories"]
    c_dir = direction(kcal, c_spec.ideal_low, c_spec.ideal_high)
    c_dist = distance_from_range(kcal, c_spec.ideal_low, c_spec.ideal_high)
    c_sev = severity(c_dist, step_small=150, step_medium=400, step_large=800)

    ideal_low = int(round(c_spec.ideal_low))
    ideal_high = int(round(c_spec.ideal_high))

    if c_dir == "within":
        messages.append(f"Calories are in your ideal range ({int(kcal)} kcal). Good balance.")
    elif c_dir == "below":
        gap = int(round(c_spec.ideal_low - kcal))
        messages.append(
            f"Calories are low ({int(kcal)} kcal). You’re about ~{gap} kcal below the ideal minimum ({ideal_low}–{ideal_high} kcal)."
        )
        if c_sev in ("large", "extreme"):
            messages.append("Try adding a proper meal or nutrient-dense snack (protein + carbs) today.")
        elif c_sev == "medium":
            messages.append("Try adding ~300–500 kcal via an extra meal/snack.")
        else:
            messages.append("Try adding ~150–300 kcal via a small snack.")
        messages.append("Tip: add protein (e.g., yogurt, eggs, chicken) to support recovery.")
        messages.append("Tip: don’t ‘make up’ calories with only sugary snacks—aim for quality.")
    else:  # above
        excess = int(round(kcal - c_spec.ideal_high))
        messages.append(
            f"Calories are high ({int(kcal)} kcal). You’re about ~{excess} kcal above the ideal maximum ({ideal_low}–{ideal_high} kcal)."
        )
        if c_sev in ("large", "extreme"):
            messages.append("Consider reducing portion sizes and cutting high-calorie snacks today.")
        elif c_sev == "medium":
            messages.append("Try reducing intake by ~300–500 kcal (e.g., remove one snack or reduce portion sizes).")
        else:
            messages.append("Try reducing intake slightly (e.g., smaller portion at one meal).")
        messages.append("Tip: swap sugary drinks/snacks for lower-calorie options to improve the score quickly.")
        messages.append("Tip: add a short walk after meals to support balance.")

    # I optionally add a “top focus” summary to make the advice feel more guided.
    # This uses the lowest subscores to tell the user what to prioritise.
    try:
        sorted_metrics = sorted(subscores.items(), key=lambda kv: kv[1])
        lowest = [m for m, _ in sorted_metrics[:2]]
        messages.insert(
            0,
            f"Top focus today: {', '.join(lowest)} (these have the lowest scores and will boost your overall score fastest).",
        )
    except Exception:
        # If anything goes wrong, I still return the per-metric advice.
        pass

    return messages