import pandas as pd

INPUT_PATH = "analytics/data/raw/queue_data.csv"


def validate_data(df):
    errors = []

    # Missing values
    if df.isnull().sum().sum() > 0:
        errors.append("Dataset contains missing values")

    # Duplicate records
    if df["record_id"].duplicated().any():
        errors.append("Duplicate record IDs found")

    # Queue validation
    if (df["queue_length"] < 0).any():
        errors.append("Negative queue length found")

    # Position validation
    if (df["position"] > df["queue_length"]).any():
        errors.append("Position cannot be greater than queue length")

    # Service time validation
    if (df["service_time"] <= 0).any():
        errors.append("Invalid service time found")

    if (df["average_service_time"] <= 0).any():
        errors.append("Invalid average service time found")

    # Wait time validation
    if (df["wait_time"] < 0).any():
        errors.append("Negative wait time found")

    # Required columns
    required_columns = [
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
        "data_source"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(
            f"Missing columns: {missing_columns}"
        )

    return errors


# Load dataset
df = pd.read_csv(INPUT_PATH)

print("\n========================================")
print("QUEUELESS DATA VALIDATION")
print("========================================")

errors = validate_data(df)

if errors:
    print("\n❌ VALIDATION FAILED")

    for error in errors:
        print(f"- {error}")

else:
    print("\n✅ VALIDATION PASSED")
    print(f"Records checked: {len(df)}")
    print(f"Columns checked: {len(df.columns)}")
    print("No data quality problems detected.")

print("\nValidation completed.")