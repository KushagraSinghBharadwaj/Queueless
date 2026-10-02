from pathlib import Path

import pandas as pd

from preprocessing import clean_data


BASE_DIR = Path(__file__).resolve().parents[2]

REAL_DATA_PATH = (
    BASE_DIR
    / "analytics"
    / "data"
    / "external"
    / "queue_data_real.csv"
)

REAL_PROCESSED_PATH = (
    BASE_DIR
    / "analytics"
    / "data"
    / "processed"
    / "queue_data_real_clean.csv"
)


REQUIRED_COLUMNS = [
    "record_id",
    "timestamp",
    "facility_id",
    "facility",
    "queue_length",
    "position",
    "people_served",
    "service_time",
    "average_service_time",
    "recent_service_rate",
    "day_of_week",
    "hour",
    "is_weekend",
    "is_peak_hour",
    "wait_time",
]


def load_real_data():

    if not REAL_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Real dataset not found: {REAL_DATA_PATH}"
        )

    df = pd.read_csv(
        REAL_DATA_PATH
    )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    return df


def process_real_data():

    df = load_real_data()

    print("\n========================================")
    print("QUEUELESS REAL DATA PIPELINE")
    print("========================================")

    print(
        f"Raw real records: {len(df)}"
    )

    clean_df = clean_data(df)

    REAL_PROCESSED_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    clean_df.to_csv(
        REAL_PROCESSED_PATH,
        index=False
    )

    print(
        f"Clean real records: {len(clean_df)}"
    )

    print(
        f"Saved to: {REAL_PROCESSED_PATH}"
    )

    return clean_df


if __name__ == "__main__":

    try:

        process_real_data()

        print(
            "\n✅ REAL DATA PIPELINE COMPLETED"
        )

    except FileNotFoundError:

        print(
            "\nNo real dataset available yet."
        )

        print(
            f"Expected file: "
            f"{REAL_DATA_PATH}"
        )

    except ValueError as error:

        print(
            f"\n❌ DATA VALIDATION ERROR"
        )

        print(error)