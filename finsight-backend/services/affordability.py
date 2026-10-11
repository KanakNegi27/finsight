
def assess_affordability(profile: dict) -> dict:
    """
    Assess whether a purchase is affordable based on
    savings, income, expenses, debt payments and reserve.
    """

    required_fields = [
        "savings",
        "monthly_income",
        "monthly_expenses",
        "monthly_debt_payments",
        "purchase_amount",
        "emergency_reserve",
    ]

    missing_fields = [
        field
        for field in required_fields
        if profile.get(field) is None
    ]

    if missing_fields:
        return {
            "recommendation": "WAIT",
            "confidence": "LOW",
            "warnings": [
                "Required financial information is missing."
            ],
            "missing_fields": missing_fields,
        }

    try:
        values = {
            field: float(profile[field])
            for field in required_fields
        }
    except (TypeError, ValueError):
        return {
            "recommendation": "WAIT",
            "confidence": "LOW",
            "warnings": ["Financial values must be valid numbers."],
            "missing_fields": [],
        }

    if any(value < 0 for value in values.values()):
        return {
            "recommendation": "WAIT",
            "confidence": "LOW",
            "warnings": ["Financial values cannot be negative."],
            "missing_fields": [],
        }

    savings = values["savings"]
    income = values["monthly_income"]
    expenses = values["monthly_expenses"]
    debt = values["monthly_debt_payments"]
    purchase = values["purchase_amount"]
    reserve = values["emergency_reserve"]

    remaining_savings = savings - purchase
    monthly_surplus = income - expenses - debt

    warnings = []

    if remaining_savings < reserve:
        warnings.append(
            "The purchase would reduce savings below "
            "the required emergency reserve."
        )

    if monthly_surplus < 0:
        warnings.append(
            "Monthly expenses and debt payments exceed income."
        )

    affordable = (
        remaining_savings >= reserve
        and monthly_surplus >= 0
    )

    return {
        "recommendation": "BUY" if affordable else "WAIT",
        "confidence": "MEDIUM",
        "remaining_savings": remaining_savings,
        "monthly_surplus": monthly_surplus,
        "warnings": warnings,
        "missing_fields": [],
    }
