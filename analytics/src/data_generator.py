import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

# Facility-specific configuration
facilities = {
    "Canteen": {
        "base_queue": 10,
        "service_time": 2.5,
        "service_variation": 0.5
    },
    "Library": {
        "base_queue": 7,
        "service_time": 4.0,
        "service_variation": 0.8
    },
    "Printing Shop": {
        "base_queue": 5,
        "service_time": 3.0,
        "service_variation": 0.6
    },
    "Admin Office": {
        "base_queue": 4,
        "service_time": 5.0,
        "service_variation": 1.0
    },
    "Computer Lab": {
        "base_queue": 8,
        "service_time": 3.5,
        "service_variation": 0.7
    },
    "Bus Stop": {
        "base_queue": 12,
        "service_time": 1.5,
        "service_variation": 0.3
    }
}

start_date = datetime(2026, 1, 1)

data = []

for i in range(5000):

    # Generate a realistic campus date and time
    day_offset = random.randint(0, 59)

    hour = random.randint(8, 17)
    minute = random.choice([0, 15, 30, 45])

    timestamp = start_date + timedelta(
        days=day_offset,
        hours=hour,
        minutes=minute
    )

    facility = random.choice(list(facilities.keys()))

    config = facilities[facility]

    day_of_week = timestamp.weekday()

    # Weekend indicator
    is_weekend = day_of_week >= 5

    # -------------------------------------------------
    # FACILITY-SPECIFIC TRAFFIC PATTERNS
    # -------------------------------------------------

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

    # Lower campus activity on weekends
    if is_weekend:
        traffic_multiplier *= 0.6

    # -------------------------------------------------
    # GENERATE QUEUE LENGTH
    # -------------------------------------------------

    expected_queue = config["base_queue"] * traffic_multiplier

    queue_length = int(
        random.gauss(
            expected_queue,
            max(2, expected_queue * 0.25)
        )
    )

    queue_length = max(0, min(queue_length, 50))

    # -------------------------------------------------
    # SERVICE TIME
    # -------------------------------------------------

    average_service_time = random.gauss(
        config["service_time"],
        config["service_variation"]
    )

    average_service_time = max(
        0.8,
        round(average_service_time, 2)
    )

    # -------------------------------------------------
    # PEOPLE SERVED
    # -------------------------------------------------

    people_served = random.randint(1, 10)

    # -------------------------------------------------
    # PEAK HOUR
    # -------------------------------------------------

    is_peak_hour = (
        (10 <= hour <= 11)
        or
        (12 <= hour <= 14)
        or
        (16 <= hour <= 17)
    )

    # -------------------------------------------------
    # WAIT TIME
    # -------------------------------------------------

    wait_time = (
        queue_length
        * average_service_time
    )

    # Add realistic variation
    wait_time += random.uniform(-8, 8)

    # Slight additional congestion during peak hours
    if is_peak_hour:
        wait_time *= random.uniform(1.05, 1.20)

    wait_time = max(
        0,
        round(wait_time, 2)
    )

    data.append({
        "timestamp": timestamp,
        "facility": facility,
        "queue_length": queue_length,
        "people_served": people_served,
        "average_service_time": average_service_time,
        "day_of_week": day_of_week,
        "hour": hour,
        "is_peak_hour": is_peak_hour,
        "wait_time": wait_time
    })


# Create DataFrame
df = pd.DataFrame(data)

# Sort chronologically
df = df.sort_values("timestamp").reset_index(drop=True)

# Save dataset
output_path = "analytics/data/raw/queue_data.csv"

df.to_csv(
    output_path,
    index=False
)

print("Dataset generated successfully!")
print(f"Records: {len(df)}")
print(f"Saved to: {output_path}")

print("\nFirst 5 rows:")
print(df.head())

print("\nFacility distribution:")
print(df["facility"].value_counts())

print("\nAverage wait time by facility:")
print(
    df.groupby("facility")["wait_time"]
    .mean()
    .round(2)
)

print("\nAverage wait time by peak hour:")
print(
    df.groupby("is_peak_hour")["wait_time"]
    .mean()
    .round(2)
)