import pandas as pd
import json

INPUT_PATH = "analytics/data/processed/queue_data_clean.csv"
OUTPUT_PATH = "analytics/outputs/analytics_summary.json"

def load_data():
    return pd.read_csv(INPUT_PATH)


def generate_analytics(df):

    analytics = {}

    # Basic statistics
    analytics["total_records"] = len(df)

    analytics["average_wait_time"] = round(
        df["wait_time"].mean(), 2
    )

    analytics["maximum_wait_time"] = round(
        df["wait_time"].max(), 2
    )

    analytics["average_queue_length"] = round(
        df["queue_length"].mean(), 2
    )

    analytics["total_people_served"] = int(
        df["people_served"].sum()
    )

    # Facility statistics
    facility_stats = (
        df.groupby("facility")
        .agg(
            average_wait_time=("wait_time", "mean"),
            average_queue_length=("queue_length", "mean"),
            average_service_time=("average_service_time", "mean"),
            total_people_served=("people_served", "sum")
        )
        .round(2)
        .sort_values(
            "average_wait_time",
            ascending=False
        )
    )

    analytics["facility_statistics"] = facility_stats

    # Peak vs non-peak
    peak_stats = (
        df.groupby("is_peak_hour")
        .agg(
            average_wait_time=("wait_time", "mean"),
            average_queue_length=("queue_length", "mean")
        )
        .round(2)
    )

    analytics["peak_statistics"] = peak_stats

    # Hourly statistics
    hourly_stats = (
        df.groupby("hour")
        .agg(
            average_wait_time=("wait_time", "mean"),
            average_queue_length=("queue_length", "mean")
        )
        .round(2)
    )

    analytics["hourly_statistics"] = hourly_stats

    return analytics


if __name__ == "__main__":

    print("\n========================================")
    print("QUEUELESS ANALYTICS")
    print("========================================")

    df = load_data()

    results = generate_analytics(df)
    summary = {
    "overall": {
        "total_records": results["total_records"],
        "average_wait_time": results["average_wait_time"],
        "maximum_wait_time": results["maximum_wait_time"],
        "average_queue_length": results["average_queue_length"],
        "total_people_served": results["total_people_served"]
    },

    "facility_statistics": (
        results["facility_statistics"]
        .reset_index()
        .to_dict(orient="records")
    ),

    "peak_statistics": (
        results["peak_statistics"]
        .reset_index()
        .to_dict(orient="records")
    ),

    "hourly_statistics": (
        results["hourly_statistics"]
        .reset_index()
        .to_dict(orient="records")
    )
}

    with open(OUTPUT_PATH, "w") as file:
        json.dump(summary, file, indent=4)

    print(f"\nAnalytics summary saved to: {OUTPUT_PATH}")

    print("\n--- OVERALL ---")
    print(f"Total records: {results['total_records']}")
    print(
        f"Average wait: "
        f"{results['average_wait_time']} minutes"
    )
    print(
        f"Maximum wait: "
        f"{results['maximum_wait_time']} minutes"
    )
    print(
        f"Average queue: "
        f"{results['average_queue_length']} people"
    )
    print(
        f"People served: "
        f"{results['total_people_served']}"
    )

    print("\n--- FACILITY STATISTICS ---")
    print(results["facility_statistics"])

    print("\n--- PEAK VS NON-PEAK ---")
    print(results["peak_statistics"])

    print("\n--- HOURLY STATISTICS ---")
    print(results["hourly_statistics"])

    print("\n✅ ANALYTICS COMPLETED")