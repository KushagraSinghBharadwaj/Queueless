from pathlib import Path

import pandas as pd

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


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
    print("QUEUELESS MODEL COMPARISON")
    print("========================================")

    df = pd.read_csv(DATASET_PATH)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp").reset_index(drop=True)

    # Feature engineering
    df["queue_pressure"] = (
        df["queue_length"] * df["average_service_time"]
    )

    df["people_ahead"] = df["position"].clip(lower=0)

    df["service_rate"] = (
        60 / df["average_service_time"]
    )

    # Convert facility into numeric columns
    df = pd.get_dummies(
        df,
        columns=["facility"],
        dtype=int
    )

    features = [
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

    X = df[features]
    y = df["wait_time"]

    # Time-aware 80/20 split
    split_index = int(len(df) * 0.80)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    models = {
        "Linear Regression": LinearRegression(),

        "Random Forest": RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
            min_samples_leaf=2,
        ),

        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        ),
    }

    results = []

    for name, model in models.items():

        print(f"\nTraining: {name}")

        model.fit(X_train, y_train)

        predictions = model.predict(X_test)

        mae = mean_absolute_error(
            y_test,
            predictions
        )

        rmse = mean_squared_error(
            y_test,
            predictions
        ) ** 0.5

        r2 = r2_score(
            y_test,
            predictions
        )

        results.append({
            "model": name,
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2": round(r2, 4),
        })

    results_df = pd.DataFrame(results)

    print("\n========================================")
    print("MODEL COMPARISON RESULTS")
    print("========================================")

    print(results_df.to_string(index=False))

    output_path = (
        BASE_DIR
        / "analytics"
        / "outputs"
        / "model_comparison.csv"
    )

    results_df.to_csv(
        output_path,
        index=False
    )

    print(f"\nResults saved to: {output_path}")

    print("\n✅ MODEL COMPARISON COMPLETED")


if __name__ == "__main__":
    main()