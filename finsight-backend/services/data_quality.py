
from datetime import datetime, timedelta


def check_data_quality(profile: dict) -> dict:
    """Check completeness and basic reliability of financial data."""

    required_fields = [
        "savings",
        "monthly_income",
        "monthly_expenses",
        "monthly_debt_payments",
        "purchase_amount",
        "emergency_reserve",
    ]

    missing_fields = []
    invalid_fields = []
    estimated_fields = []
    stale_fields = []
    warnings = []

    for field in required_fields:
        value = profile.get(field)

        if value is None:
            missing_fields.append(field)
            continue

        try:
            number = float(value)
            if number < 0:
                invalid_fields.append(field)
        except (TypeError, ValueError):
            invalid_fields.append(field)

    statuses = profile.get("field_status", {})

    for field in required_fields:
        status = statuses.get(field)

        if status == "estimated":
            estimated_fields.append(field)
        elif status == "stale":
            stale_fields.append(field)

    if missing_fields:
        warnings.append(
            "Some required financial information is missing."
        )

    if invalid_fields:
        warnings.append(
            "Some financial values are invalid or negative."
        )

    if estimated_fields:
        warnings.append(
            "Some values are estimates rather than confirmed figures."
        )

    if stale_fields:
        warnings.append(
            "Some financial information may be outdated."
        )

    supplied_count = sum(
        1 for field in required_fields
        if profile.get(field) is not None
    )

    completeness = round(
        supplied_count / len(required_fields), 2
    )

    return {
        "data_completeness": completeness,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "estimated_fields": estimated_fields,
        "stale_fields": stale_fields,
        "warnings": warnings,
        "is_valid": not missing_fields and not invalid_fields,
    }
