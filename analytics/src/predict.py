import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "analytics" / "models" / "queue_wait_model.pkl"

model = joblib.load(MODEL_PATH)

FACILITY_COLUMNS = [
    "facility_Admin Office",
    "facility_Bus Stop",
    "facility_Canteen",
    "facility_Computer Lab",
    "facility_Library",
    "facility_Printing Shop",
]

SUPPORTED_FACILITIES = {
    "Admin Office",
    "Bus Stop",
    "Canteen",
    "Computer Lab",
    "Library",
    "Printing Shop",
}


def predict_wait_time(
    queue_length,
    people_served,
    average_service_time,
    day_of_week,
    hour,
    is_peak_hour,
    facility,
):
    if facility not in SUPPORTED_FACILITIES:
        raise ValueError(
            f"Unsupported facility '{facility}'. "
            f"Expected one of: {sorted(SUPPORTED_FACILITIES)}"
        )

    input_data = {
        "queue_length": float(queue_length),
        "people_served": float(people_served),
        "average_service_time": float(average_service_time),
        "day_of_week": int(day_of_week),
        "hour": int(hour),
        "is_peak_hour": int(is_peak_hour),
    }

    for column in FACILITY_COLUMNS:
        input_data[column] = int(column == f"facility_{facility}")

    input_df = pd.DataFrame([input_data])
    prediction = float(model.predict(input_df)[0])

    return round(max(0.0, prediction), 2)


if __name__ == "__main__":
    predicted_wait = predict_wait_time(
        queue_length=15,
        people_served=5,
        average_service_time=2.5,
        day_of_week=2,
        hour=13,
        is_peak_hour=True,
        facility="Canteen",
    )

    print("Model loaded successfully!")
    print(f"Predicted wait time: {predicted_wait} minutes")
