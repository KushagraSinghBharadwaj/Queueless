from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_PATH = (
    BASE_DIR
    / "analytics"
    / "data"
    / "raw"
    / "queue_data.csv"
)

PROCESSED_PATH = (
    BASE_DIR
    / "analytics"
    / "data"
    / "processed"
    / "queue_data_clean.csv"
)


def clean_data(df):

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove duplicate records
    df = df.drop_duplicates(
        subset=["record_id"]
    )

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # Ensure numeric columns are numeric
    numeric_columns = [
        "queue_length",
        "position",
        "people_served",
        "service_time",
        "average_service_time",
        "recent_service_rate",
        "day_of_week",
        "hour",
        "wait_time",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Remove rows with invalid timestamps
    df = df.dropna(
        subset=["timestamp"]
    )

    # Remove invalid records
    df = df[
        (df["queue_length"] >= 0)
        & (df["position"] >= 0)
        & (df["position"] <= df["queue_length"])
        & (df["service_time"] > 0)
        & (df["average_service_time"] > 0)
        & (df["recent_service_rate"] > 0)
        & (df["wait_time"] >= 0)
    ]

    # Sort chronologically
    df = df.sort_values(
        "timestamp"
    )

    # Reset index
    df = df.reset_index(drop=True)

    return df


def process_file(input_path, output_path):

    df = pd.read_csv(input_path)

    print("\n========================================")
    print("QUEUELESS DATA PREPROCESSING")
    print("========================================")

    print(f"Input file: {input_path}")
    print(f"Raw records: {len(df)}")

    clean_df = clean_data(df)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    clean_df.to_csv(
        output_path,
        index=False
    )

    print(f"Clean records: {len(clean_df)}")
    print(
        f"Removed records: "
        f"{len(df) - len(clean_df)}"
    )

    print(f"Saved to: {output_path}")

    return clean_df


if __name__ == "__main__":

    process_file(
        RAW_PATH,
        PROCESSED_PATH
    )

    print(
        "\n✅ DATA PREPROCESSING COMPLETED"
    )