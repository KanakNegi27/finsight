
from statistics import median


def estimate_missing_expenses(
    profile: dict,
    historical_expenses: list[float] | None = None,
) -> dict:
    """
    Estimate missing monthly expenses from historical data.

    Requires at least 3 valid historical monthly totals.
    Does not overwrite the user's original financial profile.
    """

    actual_expenses = profile.get("monthly_expenses")

    if actual_expenses is not None:
        try:
            actual_expenses = float(actual_expenses)
        except (TypeError, ValueError):
            return {
                "estimated": False,
                "value": None,
                "range": None,
                "warnings": [
                    "Monthly expenses contain an invalid value."
                ],
            }

        if actual_expenses < 0:
            return {
                "estimated": False,
                "value": None,
                "range": None,
                "warnings": [
                    "Monthly expenses cannot be negative."
                ],
            }

        return {
            "estimated": False,
            "value": actual_expenses,
            "range": None,
            "warnings": [],
            "message": "Existing expense value retained.",
        }

    if not historical_expenses:
        return {
            "estimated": False,
            "value": None,
            "range": None,
            "warnings": [
                "Expenses are missing and no historical data is available."
            ],
        }

    valid_values = []

    for item in historical_expenses:
        if isinstance(item, bool):
            continue

        try:
            value = float(item)
        except (TypeError, ValueError):
            continue

        if value >= 0:
            valid_values.append(value)

    if len(valid_values) < 3:
        return {
            "estimated": False,
            "value": None,
            "range": None,
            "warnings": [
                "At least 3 valid historical monthly totals are "
                "required for an estimate."
            ],
        }

    estimate = float(median(valid_values))

    # A simple historical variability range.
    # This is a descriptive range, not a statistical confidence interval.
    low = float(min(valid_values))
    high = float(max(valid_values))

    return {
        "estimated": True,
        "value": estimate,
        "range": {
            "min": low,
            "max": high,
        },
        "warnings": [
            "Monthly expenses are estimated from historical data.",
            "The historical range is not a guaranteed future range.",
        ],
        "historical_months_used": len(valid_values),
    }
