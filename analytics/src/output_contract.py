from datetime import datetime


def create_prediction_response(
    facility,
    predicted_wait_minutes,
    lower_bound_minutes,
    upper_bound_minutes,
):
    """
    Create the standard response sent
    from the AI/analytics layer to the backend.
    """

    return {
        "facility": facility,
        "predicted_wait_minutes": predicted_wait_minutes,
        "estimated_range": {
            "lower_minutes": lower_bound_minutes,
            "upper_minutes": upper_bound_minutes,
        },
        "prediction_unit": "minutes",
        "generated_at": datetime.now().isoformat(),
        "model_status": "active",
    }


if __name__ == "__main__":

    response = create_prediction_response(
        facility="Canteen",
        predicted_wait_minutes=25.4,
        lower_bound_minutes=21.8,
        upper_bound_minutes=29.7,
    )

    print("\n========================================")
    print("QUEUELESS ML OUTPUT CONTRACT")
    print("========================================")

    print(response)

    print("\n✅ OUTPUT CONTRACT CREATED")