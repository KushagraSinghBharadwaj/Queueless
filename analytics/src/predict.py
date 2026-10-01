import joblib
import pandas as pd
MODEL_PATH = "analytics/models/queue_wait_model.pkl"

model = joblib.load(MODEL_PATH)

print("Model loaded successfully!")


def predict_wait_time(
    queue_length,
    people_served,
    average_service_time,
    day_of_week,
    hour,
    is_peak_hour,
    facility
):
    facility_columns = [
        "facility_Admin Office",
        "facility_Bus Stop",
        "facility_Canteen",
        "facility_Computer Lab",
        "facility_Library",
        "facility_Printing Shop"
    ]

    input_data = {
        "queue_length": queue_length,
        "people_served": people_served,
        "average_service_time": average_service_time,
        "day_of_week": day_of_week,
        "hour": hour,
        "is_peak_hour": int(is_peak_hour)
    }

    for column in facility_columns:
        input_data[column] = int(column == f"facility_{facility}")

    input_df = pd.DataFrame([input_data])

    prediction = model.predict(input_df)[0]
    return round(prediction, 2)

if __name__ == "__main__":
    predicted_wait = predict_wait_time(
        queue_length=15,
        people_served=5,
        average_service_time=2.5,
        day_of_week=2,
        hour=13,
        is_peak_hour=True,
        facility="Canteen"
    )

    print(f"Predicted wait time: {predicted_wait} minutes")