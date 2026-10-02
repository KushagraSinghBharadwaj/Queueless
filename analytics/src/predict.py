from pathlib import Path

import joblib
import pandas as pd

from output_contract import create_prediction_response


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR
    / "analytics"
    / "models"
    / "queue_wait_model.pkl"
)


FEATURE_COLUMNS = [
    "queue_length",
    "position",
    "people_served",
    "average_service_time",
    "recent_service_rate",
    "day_of_week",
    "hour",
    "is_weekend",
    "is_peak_hour",
    "queue_pressure",
    "people_ahead",
    "service_rate",
    "facility_Admin Office",
    "facility_Bus Stop",
    "facility_Canteen",
    "facility_Computer Lab",
    "facility_Library",
    "facility_Printing Shop",
]


def load_model():
    return joblib.load(MODEL_PATH)


def prepare_input(
    facility,
    queue_length,
    position,
    people_served,
    average_service_time,
    day_of_week,
    hour,
):

    data = {
        "queue_length": queue_length,
        "position": position,
        "people_served": people_served,
        "average_service_time": average_service_time,
        "recent_service_rate": 60 / average_service_time,
        "day_of_week": day_of_week,
        "hour": hour,
        "is_weekend": int(day_of_week >= 5),
        "is_peak_hour": int(
            hour in [10, 11, 12, 13, 14, 16, 17]
        ),
        "queue_pressure": (
            queue_length * average_service_time
        ),
        "people_ahead": max(position, 0),
        "service_rate": 60 / average_service_time,
    }

    facilities = [
        "Admin Office",
        "Bus Stop",
        "Canteen",
        "Computer Lab",
        "Library",
        "Printing Shop",
    ]

    for name in facilities:
        data[f"facility_{name}"] = int(
            facility == name
        )

    return pd.DataFrame([data])[FEATURE_COLUMNS]


def predict_wait_time(
    facility,
    queue_length,
    position,
    people_served,
    average_service_time,
    day_of_week,
    hour,
):

    model = load_model()

    X = prepare_input(
        facility=facility,
        queue_length=queue_length,
        position=position,
        people_served=people_served,
        average_service_time=average_service_time,
        day_of_week=day_of_week,
        hour=hour,
    )

    # Individual predictions from all Random Forest trees
    tree_predictions = [
    tree.predict(X.values)[0]
    for tree in model.estimators_
]

    prediction = sum(tree_predictions) / len(tree_predictions)

    lower_bound = pd.Series(tree_predictions).quantile(0.10)
    upper_bound = pd.Series(tree_predictions).quantile(0.90)

    return create_prediction_response(
    facility=facility,
    predicted_wait_minutes=round(float(prediction), 2),
    lower_bound_minutes=round(float(lower_bound), 2),
    upper_bound_minutes=round(float(upper_bound), 2),
)


if __name__ == "__main__":

    prediction = predict_wait_time(
    facility="Canteen",
    queue_length=30,
    position=25,
    people_served=80,
    average_service_time=2.5,
    day_of_week=2,
    hour=13,
)

    print("\n========================================")
    print("QUEUELESS WAIT TIME PREDICTION")
    print("========================================")

    print(
        f"\nPredicted wait: "
        f"{prediction['predicted_wait_minutes']} minutes"
    )

    print(
    f"Estimated range: "
    f"{prediction['estimated_range']['lower_minutes']} - "
    f"{prediction['estimated_range']['upper_minutes']} minutes"
)