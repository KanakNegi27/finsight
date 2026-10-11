
def forecast_cash_flow(
    profile: dict,
    days: int = 90,
) -> dict:
    """
    Generate a simple cash-flow forecast.

    Assumes monthly income, expenses and debt payments
    are evenly distributed across 30-day periods.

    Pending refunds are excluded from the baseline forecast.
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
            "success": False,
            "missing_fields": missing_fields,
            "warnings": [
                "Forecast unavailable until required "
                "financial information is provided."
            ],
            "periods": [],
        }

    try:
        values = {
            field: float(profile[field])
            for field in required_fields
        }
    except (TypeError, ValueError):
        return {
            "success": False,
            "missing_fields": [],
            "warnings": ["Financial values must be valid numbers."],
            "periods": [],
        }

    if any(value < 0 for value in values.values()):
        return {
            "success": False,
            "missing_fields": [],
            "warnings": ["Financial values cannot be negative."],
            "periods": [],
        }

    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        return {
            "success": False,
            "missing_fields": [],
            "warnings": ["Forecast days must be a positive integer."],
            "periods": [],
        }

    balance = values["savings"]
    monthly_income = values["monthly_income"]
    monthly_expenses = values["monthly_expenses"]
    monthly_debt = values["monthly_debt_payments"]
    purchase = values["purchase_amount"]
    reserve = values["emergency_reserve"]

    periods = []
    warnings = []

    # Apply the one-time purchase at the start of the forecast.
    balance -= purchase

    if balance < reserve:
        warnings.append(
            "Savings fall below the emergency reserve "
            "immediately after the purchase."
        )

    elapsed = 0

    while elapsed < days:
        period_days = min(30, days - elapsed)

        # Prorate monthly values for partial 30-day periods.
        fraction = period_days / 30

        income = monthly_income * fraction
        expenses = monthly_expenses * fraction
        debt_payments = monthly_debt * fraction

        opening_balance = balance
        balance += income - expenses - debt_payments

        periods.append({
            "day_start": elapsed + 1,
            "day_end": elapsed + period_days,
            "opening_balance": round(opening_balance, 2),
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "debt_payments": round(debt_payments, 2),
            "closing_balance": round(balance, 2),
            "below_reserve": balance < reserve,
        })

        elapsed += period_days

    if any(period["below_reserve"] for period in periods):
        warnings.append(
            "The projected balance falls below the "
            "required emergency reserve."
        )

    return {
        "success": True,
        "forecast_days": days,
        "initial_savings": values["savings"],
        "purchase_amount": purchase,
        "emergency_reserve": reserve,
        "final_balance": round(balance, 2),
        "minimum_projected_balance": round(
            min(
                [values["savings"] - purchase]
                + [p["closing_balance"] for p in periods]
            ),
            2,
        ),
        "periods": periods,
        "warnings": warnings,
    }

