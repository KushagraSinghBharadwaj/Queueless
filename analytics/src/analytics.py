import pandas as pd


# Load the raw dataset
df = pd.read_csv("analytics/data/raw/queue_data.csv")


# Basic dataset information
print("\n--- DATASET SHAPE ---")
print(df.shape)


# Column information
print("\n--- COLUMNS ---")
print(df.columns.tolist())


# Check missing values
print("\n--- MISSING VALUES ---")
print(df.isnull().sum())


# Basic statistics
print("\n--- STATISTICS ---")
print(df.describe())


# Average wait time by facility
print("\n--- AVERAGE WAIT TIME BY FACILITY ---")
print(
    df.groupby("facility")["wait_time"]
    .mean()
    .sort_values(ascending=False)
)


# Average queue length during peak vs non-peak hours
print("\n--- PEAK VS NON-PEAK ---")
print(
    df.groupby("is_peak_hour")["queue_length"]
    .mean()
)


# Relationship between queue length and waiting time
print("\n--- CORRELATION ---")
print(
    df[[
        "queue_length",
        "average_service_time",
        "wait_time"
    ]].corr()
)