import pandas as pd


# Load the dataset
df = pd.read_csv("analytics/data/raw/queue_data.csv")


# Convert facility names into numerical columns
df = pd.get_dummies(
    df,
    columns=["facility"],
    dtype=int
)


# Select features for the ML model
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


# Create feature matrix
X = df[features]


# Create target variable
y = df["wait_time"]


print("Features prepared successfully!")
print(f"Number of features: {X.shape[1]}")
print(f"Number of records: {X.shape[0]}")
print("\nFeature columns:")
print(X.columns.tolist())