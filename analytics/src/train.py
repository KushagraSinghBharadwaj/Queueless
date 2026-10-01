import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# --------------------------------------------------
# 1. LOAD DATASET
# --------------------------------------------------

df = pd.read_csv("analytics/data/raw/queue_data.csv")


# --------------------------------------------------
# 2. ENCODE FACILITY
# --------------------------------------------------

df = pd.get_dummies(
    df,
    columns=["facility"],
    dtype=int
)


# --------------------------------------------------
# 3. SELECT FEATURES
# --------------------------------------------------

features = [
    "queue_length",
    "people_served",
    "average_service_time",
    "day_of_week",
    "hour",
    "is_peak_hour",
    "facility_Admin Office",
    "facility_Bus Stop",
    "facility_Canteen",
    "facility_Computer Lab",
    "facility_Library",
    "facility_Printing Shop"
]

X = df[features]
y = df["wait_time"]


# --------------------------------------------------
# 4. TRAIN / TEST SPLIT
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


# --------------------------------------------------
# 5. CREATE RANDOM FOREST MODEL
# --------------------------------------------------

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)


# --------------------------------------------------
# 6. TRAIN MODEL
# --------------------------------------------------

model.fit(X_train, y_train)


# --------------------------------------------------
# 7. MAKE PREDICTIONS
# --------------------------------------------------

predictions = model.predict(X_test)


# --------------------------------------------------
# 8. EVALUATE MODEL
# --------------------------------------------------

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


print("\nRandom Forest Results")
print("-------------------------")
print(f"MAE:  {mae:.2f} minutes")
print(f"RMSE: {rmse:.2f} minutes")
print(f"R²:   {r2:.4f}")


# --------------------------------------------------
# 9. FEATURE IMPORTANCE
# --------------------------------------------------

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)


print("\nFeature Importance")
print("-------------------------")
print(importance.to_string(index=False))


# --------------------------------------------------
# 10. SAVE TRAINED MODEL
# --------------------------------------------------

model_path = "analytics/models/queue_wait_model.pkl"

joblib.dump(
    model,
    model_path
)

print(f"\nModel saved to: {model_path}")