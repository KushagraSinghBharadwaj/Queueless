import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

# ---------------------------------------------------------
# FACILITY CONFIGURATION
# ---------------------------------------------------------

facilities = {
    "Canteen": {
        "id": "CANTEEN",
        "base_queue": 10,
        "service_time": 2.5,
        "service_variation": 0.5
    },
    "Library": {
        "id": "LIBRARY",
        "base_queue": 7,
        "service_time": 4.0,
        "service_variation": 0.8
    },
    "Printing Shop": {
        "id": "PRINT",
        "base_queue": 5,
        "service_time": 3.0,
        "service_variation": 0.6
    },
    "Admin Office": {
        "id": "ADMIN",
        "base_queue": 4,
        "service_time": 5.0,
        "service_variation": 1.0
    },
    "Computer Lab": {
        "id": "LAB",
        "base_queue": 8,
        "service_time": 3.5,
        "service_variation": 0.7
    },
    "Bus Stop": {
        "id": "BUS",
        "base_queue": 12,
        "service_time": 1.5,
        "service_variation": 0.3
    }
}

START_DATE = datetime(2026, 1, 1)
NUMBER_OF_RECORDS = 2000

data = []

# ---------------------------------------------------------
# DATA GENERATION
# ---------------------------------------------------------

for i in range(NUMBER_OF_RECORDS):

    day_offset = random.randint(0, 59)

    hour = random.randint(8, 17)
    minute = random.choice([0, 15, 30, 45])

    timestamp = START_DATE + timedelta(
        days=day_offset,
        hours=hour,
        minutes=minute
    )

    facility = random.choice(list(facilities.keys()))
    config = facilities[facility]

    day_of_week = timestamp.weekday()
    is_weekend = day_of_week >= 5

    # -----------------------------------------------------
    # FACILITY TRAFFIC PATTERNS
    # -----------------------------------------------------

    traffic_multiplier = 1.0

    if facility == "Canteen":
        if 12 <= hour <= 14:
            traffic_multiplier = 2.5
        elif 16 <= hour <= 17:
            traffic_multiplier = 1.5

    elif facility == "Library":
        if 9 <= hour <= 11:
            traffic_multiplier = 1.4
        elif 14 <= hour <= 17:
            traffic_multiplier = 1.6

    elif facility == "Printing Shop":
        if 10 <= hour <= 12:
            traffic_multiplier = 1.5
        elif 15 <= hour <= 17:
            traffic_multiplier = 1.7

    elif facility == "Admin Office":
        if 10 <= hour <= 12:
            traffic_multiplier = 1.8
        elif 14 <= hour <= 16:
            traffic_multiplier = 1.3

    elif facility == "Computer Lab":
        if 10 <= hour <= 12:
            traffic_multiplier = 1.5
        elif 14 <= hour <= 16:
            traffic_multiplier = 1.6

    elif facility == "Bus Stop":
        if 8 <= hour <= 9:
            traffic_multiplier = 2.0
        elif 13 <= hour <= 14:
            traffic_multiplier = 1.5
        elif 16 <= hour <= 17:
            traffic_multiplier = 2.2

    # Lower activity on weekends
    if is_weekend:
        traffic_multiplier *= 0.6

    # -----------------------------------------------------
    # QUEUE LENGTH
    # -----------------------------------------------------

    expected_queue = config["base_queue"] * traffic_multiplier

    queue_length = int(
        random.gauss(
            expected_queue,
            max(2, expected_queue * 0.25)
        )
    )

    queue_length = max(0, min(queue_length, 50))

    # -----------------------------------------------------
    # SERVICE TIME
    # -----------------------------------------------------

    service_time = random.gauss(
        config["service_time"],
        config["service_variation"]
    )

    service_time = max(0.8, round(service_time, 2))

    # Average service time with small historical variation
    average_service_time = round(
        max(
            0.8,
            random.gauss(
                config["service_time"],
                config["service_variation"] * 0.5
            )
        ),
        2
    )

    # -----------------------------------------------------
    # SERVICE RATE
    # -----------------------------------------------------

    # Approximate number of people that can be served per hour
    recent_service_rate = round(
        60 / average_service_time,
        2
    )

    # -----------------------------------------------------
    # PEOPLE SERVED
    # -----------------------------------------------------

    expected_people_served = (
        recent_service_rate / 4
    )

    people_served = max(
        0,
        int(
            random.gauss(
                expected_people_served,
                max(1, expected_people_served * 0.2)
            )
        )
    )

    # -----------------------------------------------------
    # POSITION
    # -----------------------------------------------------

    if queue_length > 0:
        position = random.randint(1, queue_length)
    else:
        position = 0

    # -----------------------------------------------------
    # PEAK HOUR
    # -----------------------------------------------------

    is_peak_hour = (
        (10 <= hour <= 11)
        or
        (12 <= hour <= 14)
        or
        (16 <= hour <= 17)
    )

    # -----------------------------------------------------
    # WAIT TIME
    # -----------------------------------------------------

    # Approximate waiting time based on people ahead
    wait_time = (
        queue_length
        * average_service_time
    )

    # Small real-world variation
    wait_time += random.uniform(-5, 5)

    # Congestion during peak periods
    if is_peak_hour:
        wait_time *= random.uniform(1.05, 1.15)

    # Weekend activity is lower
    if is_weekend:
        wait_time *= random.uniform(0.85, 0.95)

    wait_time = max(
        0,
        round(wait_time, 2)
    )

    # -----------------------------------------------------
    # RECORD
    # -----------------------------------------------------

    data.append({
        "record_id": f"QL-{i + 1:06d}",
        "timestamp": timestamp,
        "facility_id": config["id"],
        "facility": facility,
        "queue_length": queue_length,
        "position": position,
        "people_served": people_served,
        "service_time": service_time,
        "average_service_time": average_service_time,
        "recent_service_rate": recent_service_rate,
        "day_of_week": day_of_week,
        "hour": hour,
        "is_weekend": is_weekend,
        "is_peak_hour": is_peak_hour,
        "wait_time": wait_time,
        "data_source": "synthetic"
    })


# ---------------------------------------------------------
# CREATE DATAFRAME
# ---------------------------------------------------------

df = pd.DataFrame(data)

# Sort chronologically
df = df.sort_values("timestamp").reset_index(drop=True)

# ---------------------------------------------------------
# SAVE DATASET
# ---------------------------------------------------------

output_path = "analytics/data/raw/queue_data.csv"

df.to_csv(
    output_path,
    index=False
)

# ---------------------------------------------------------
# REPORT
# ---------------------------------------------------------

print("\n========================================")
print("QUEUELESS DATASET GENERATED")
print("========================================")

print(f"Records: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Saved to: {output_path}")

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 records:")
print(df.head())

print("\nFacility distribution:")
print(df["facility"].value_counts())

print("\nAverage wait time by facility:")
print(
    df.groupby("facility")["wait_time"]
    .mean()
    .round(2)
)

print("\nAverage queue by facility:")
print(
    df.groupby("facility")["queue_length"]
    .mean()
    .round(2)
)

print("\nPeak vs non-peak:")
print(
    df.groupby("is_peak_hour")["wait_time"]
    .mean()
    .round(2)
)

print("\nDataset generation completed successfully!")