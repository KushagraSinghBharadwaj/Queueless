import pandas as pd


def create_features(df):

    data = df.copy()

    # Convert timestamp
    data["timestamp"] = pd.to_datetime(data["timestamp"])

    # Time-based features
    data["day_of_week"] = data["timestamp"].dt.dayofweek
    data["hour"] = data["timestamp"].dt.hour
    data["is_weekend"] = (data["day_of_week"] >= 5).astype(int)

    # Peak hour
    data["is_peak_hour"] = (
        data["hour"].isin([10, 11, 12, 13, 14, 16, 17])
    ).astype(int)

    # Queue pressure
    data["queue_pressure"] = (
        data["queue_length"] * data["average_service_time"]
    )

    # People ahead of the user
    data["people_ahead"] = data["position"].clip(lower=0)

    # Service efficiency
    data["service_rate"] = (
        60 / data["average_service_time"]
    )

    # Facility encoding
    data = pd.get_dummies(
        data,
        columns=["facility"],
        dtype=int
    )

    return data