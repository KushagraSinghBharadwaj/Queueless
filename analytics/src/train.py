import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = BASE_DIR / "analytics" / "data" / "raw" / "queue_data.csv"
MODEL_PATH = BASE_DIR / "analytics" / "models" / "queue_wait_model.pkl"
METADATA_PATH = BASE_DIR / "analytics" / "models" / "model_metadata.json"

FEATURES = [
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


def main():
    df = pd.read_csv(DATASET_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp").reset_index(drop=True)
    df["queue_pressure"] = (
    df["queue_length"] * df["average_service_time"]
)

    df["people_ahead"] = (
        df["position"].clip(lower=0)
    )

    df["service_rate"] = (
        60 / df["average_service_time"]
    )
    df = pd.get_dummies(df, columns=["facility"], dtype=int)

    missing = [feature for feature in FEATURES if feature not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing model features: {missing}")

    X = df[FEATURES]
    y = df["wait_time"]

    # Time-aware train/test split
    split_index = int(len(df) * 0.80)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    model = RandomForestRegressor(
        n_estimators=50,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,
    )

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, predictions))
    rmse = float(mean_squared_error(y_test, predictions) ** 0.5)
    r2 = float(r2_score(y_test, predictions))

    importance = (
        pd.DataFrame(
            {
                "feature": FEATURES,
                "importance": model.feature_importances_,
            }
        )
        .sort_values("importance", ascending=False)
    )

    metadata = {
        "model": "RandomForestRegressor",
        "training_records": int(len(df)),
        "test_records": int(len(X_test)),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "features": FEATURES,
        "feature_importance": [
            {
                "feature": row["feature"],
                "importance": round(float(row["importance"]), 6),
            }
            for _, row in importance.iterrows()
        ],
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\nRandom Forest Results")
    print("-------------------------")
    print(f"Training records: {len(df)}")
    print(f"Test records:     {len(X_test)}")
    print(f"MAE:              {mae:.2f} minutes")
    print(f"RMSE:             {rmse:.2f} minutes")
    print(f"R²:               {r2:.4f}")

    print("\nFeature Importance")
    print("-------------------------")
    print(importance.to_string(index=False))

    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Metadata saved to: {METADATA_PATH}")


if __name__ == "__main__":
    main()
