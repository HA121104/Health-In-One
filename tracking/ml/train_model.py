from __future__ import annotations

from pathlib import Path
import random

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from tracking.services.scoring import compute_overall_score, compute_subscores, clamp_score


MODEL_VERSION = "ml_random_forest_v1"

FEATURE_NAMES = [
    "age",
    "height_cm",
    "weight_kg",
    "activity_level_encoded",
    "health_goal_encoded",
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
    "avg_7_day_score",
    "avg_30_day_score",
]

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
    I convert activity level text into a number because machine learning models
    need numeric inputs rather than string labels.
    """
    return ACTIVITY_MAP.get(activity_level, ACTIVITY_MAP["MODERATE"])


def encode_goal(health_goal: str) -> int:
    """
    I convert the user's health goal into a numeric value so it can be used as
    a model feature.
    """
    return GOAL_MAP.get(health_goal, GOAL_MAP["GENERAL"])


def generate_training_row(rng: np.random.Generator) -> tuple[list[float], int]:
    """
    I generate realistic synthetic training examples because the app does not
    yet have months of real user data.

    The important point is that the generated data follows the same structure
    as the real app data, so the ML model learns how profile data, daily metrics
    and history relate to the final score.
    """
    activity_level = random.choice(list(ACTIVITY_MAP.keys()))
    health_goal = random.choice(list(GOAL_MAP.keys()))

    age = int(rng.integers(18, 70))
    height_cm = int(rng.integers(150, 200))
    weight_kg = float(np.clip(rng.normal(75, 18), 45, 140))

    calories_kcal = int(rng.integers(900, 5000))
    water_ml = int(rng.integers(0, 6500))
    sleep_hours = round(float(rng.uniform(3, 12)), 1)
    exercise_minutes = int(rng.integers(0, 220))
    steps = int(rng.integers(0, 30000))
    screen_time_hours = round(float(rng.uniform(0, 15)), 1)
    stress_level = int(rng.integers(1, 11))
    mood_level = int(rng.integers(1, 11))
    energy_level = int(rng.integers(1, 11))
    fruit_veg_servings = int(rng.integers(0, 13))
    protein_grams = int(rng.integers(0, 260))

    subscores = compute_subscores(
        calories_kcal=calories_kcal,
        water_ml=water_ml,
        sleep_hours=sleep_hours,
        exercise_minutes=exercise_minutes,
        steps=steps,
        screen_time_hours=screen_time_hours,
        stress_level=stress_level,
        mood_level=mood_level,
        energy_level=energy_level,
        fruit_veg_servings=fruit_veg_servings,
        protein_grams=protein_grams,
        activity_level=activity_level,
        weight_kg=weight_kg,
        health_goal=health_goal,
    )

    current_score = compute_overall_score(subscores)

    # I include history because the final feedback asked for more meaningful long-term tracking.
    # These values simulate how a user's recent averages can influence prediction.
    avg_7_day_score = clamp_score(current_score + rng.normal(0, 15))
    avg_30_day_score = clamp_score(avg_7_day_score + rng.normal(0, 10))

    # I make the target mostly based on today's score, but also influenced by history.
    # This makes the ML model learn from both today's behaviour and longer-term consistency.
    target_score = clamp_score(
        (current_score * 0.78)
        + (avg_7_day_score * 0.15)
        + (avg_30_day_score * 0.07)
        + rng.normal(0, 2)
    )

    row = [
        age,
        height_cm,
        weight_kg,
        encode_activity(activity_level),
        encode_goal(health_goal),
        calories_kcal,
        water_ml,
        sleep_hours,
        exercise_minutes,
        steps,
        screen_time_hours,
        stress_level,
        mood_level,
        energy_level,
        fruit_veg_servings,
        protein_grams,
        avg_7_day_score,
        avg_30_day_score,
    ]

    return row, target_score


def train_model(sample_count: int = 5000) -> None:
    """
    I train a Random Forest Regressor because it can learn non-linear patterns
    between health metrics and predicted health score.

    This is more meaningful than basic if/else advice because the final
    recommendation is based on predicted score improvements.
    """
    rng = np.random.default_rng(42)

    rows = []
    targets = []

    for _ in range(sample_count):
        row, target = generate_training_row(rng)
        rows.append(row)
        targets.append(target)

    X = np.array(rows)
    y = np.array(targets)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = RandomForestRegressor(
        # I use a smaller forest so the saved model stays below GitHub's 100MB file limit.
        # This keeps the project easy for examiners to clone without needing Git LFS.
        n_estimators=60,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    artifact = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "model_version": MODEL_VERSION,
        "metrics": {
            "mae": round(float(mae), 3),
            "r2_score": round(float(r2), 3),
            "sample_count": sample_count,
        },
    }

    output_dir = Path(__file__).resolve().parents[1] / "ml_artifacts"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "health_score_model.joblib"
    joblib.dump(artifact, output_path)

    print("ML model trained successfully.")
    print(f"Saved model to: {output_path}")
    print(f"MAE: {mae:.3f}")
    print(f"R2 score: {r2:.3f}")


if __name__ == "__main__":
    # I keep the script runnable from the command line so I can retrain the model easily.
    train_model()