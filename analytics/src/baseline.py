from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    BASE_DIR
    / "analytics"
    / "data"
    / "processed"
    / "queue_data_clean.csv"
)


def main():

    print("\n========================================")
    print("QUEUELESS BASELINE EVALUATION")
    print("========================================")

    df = pd.read_csv(DATASET_PATH)

    # Simple queueing formula:
    # estimated wait = people ahead × average service time
    baseline_predictions = (
        df["position"]
        * df["average_service_time"]
    )

    actual = df["wait_time"]

    mae = mean_absolute_error(
        actual,
        baseline_predictions
    )

    rmse = mean_squared_error(
        actual,
        baseline_predictions
    ) ** 0.5

    print(f"\nRecords evaluated: {len(df)}")

    print("\nBaseline Results")
    print("----------------------------------------")
    print(f"MAE:  {mae:.2f} minutes")
    print(f"RMSE: {rmse:.2f} minutes")

    print("\n✅ BASELINE EVALUATION COMPLETED")


if __name__ == "__main__":
    main()