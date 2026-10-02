from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error


BASE_DIR = Path(__file__).resolve().parents[2]

REAL_DATA_PATH = (
    BASE_DIR
    / "analytics"
    / "data"
    / "processed"
    / "queue_data_real_clean.csv"
)

MODEL_PATH = (
    BASE_DIR
    / "analytics"
    / "models"
    / "queue_wait_model.pkl"
)


MIN_NEW_RECORDS = 100
MAX_ACCEPTABLE_MAE = 10.0


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


def prepare_features(df):

    df = df.copy()

    df["queue_pressure"] = (
        df["queue_length"]
        * df["average_service_time"]
    )

    df["people_ahead"] = (
        df["position"].clip(lower=0)
    )

    df["service_rate"] = (
        60 / df["average_service_time"]
    )

    df = pd.get_dummies(
        df,
        columns=["facility"],
        prefix="facility"
    )

    for column in FEATURE_COLUMNS:

        if column not in df.columns:
            df[column] = 0

    return df[FEATURE_COLUMNS]


def check_retraining_needed():

    print("\n========================================")
    print("QUEUELESS RETRAINING CHECK")
    print("========================================")

    if not REAL_DATA_PATH.exists():

        print(
            "\n❌ Real processed dataset not found."
        )

        return

    df = pd.read_csv(
        REAL_DATA_PATH
    )

    new_records = len(df)

    print(
        f"\nNew real records available: "
        f"{new_records}"
    )

    print(
        f"Minimum records required: "
        f"{MIN_NEW_RECORDS}"
    )

    if new_records < MIN_NEW_RECORDS:

        remaining = (
            MIN_NEW_RECORDS - new_records
        )

        print(
            "\n⏳ RETRAINING NOT REQUIRED YET"
        )

        print(
            f"Additional records needed: "
            f"{remaining}"
        )

        return

    if not MODEL_PATH.exists():

        print(
            "\n⚠️ Existing model not found."
        )

        print(
            "Retraining should be performed."
        )

        return

    model = joblib.load(
        MODEL_PATH
    )

    X = prepare_features(df)

    actual = df["wait_time"]

    predictions = model.predict(X)

    mae = mean_absolute_error(
        actual,
        predictions
    )

    print(
        f"\nCurrent model MAE on real data: "
        f"{mae:.2f} minutes"
    )

    print(
        f"Maximum acceptable MAE: "
        f"{MAX_ACCEPTABLE_MAE:.2f} minutes"
    )

    if mae > MAX_ACCEPTABLE_MAE:

        print(
        "\n🔄 RETRAINING RECOMMENDED"
        )

        print(
            "Model performance on real data "
            "is below the acceptable threshold."
        )

    else:

        print(
            "\n✅ CURRENT MODEL PERFORMANCE ACCEPTABLE"
        )

        print(
            "Retraining is not required yet."
        )


if __name__ == "__main__":

    check_retraining_needed()