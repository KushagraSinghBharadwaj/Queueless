import pandas as pd
from sklearn.metrics import mean_absolute_error


# Load dataset
df = pd.read_csv("analytics/data/raw/queue_data.csv")


# Calculate baseline prediction
df["baseline_wait_time"] = (
    df["queue_length"] *
    df["average_service_time"]
)


# Calculate error
mae = mean_absolute_error(
    df["wait_time"],
    df["baseline_wait_time"]
)


print("Baseline Model")
print("-------------------------")
print(f"Mean Absolute Error: {mae:.2f} minutes")