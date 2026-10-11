from services.analysis import analyze_purchases_30_days


def base_profile():
    return {
        "savings": 100000,
        "monthly_income": 50000,
        "monthly_expenses": 20000,
        "monthly_debt_payments": 5000,
        "emergency_reserve": 20000,
    }


def test_no_purchases_grows_balance():
    result = analyze_purchases_30_days(base_profile(), [])

    assert result["success"] is True
    assert result["total_spend"] == 0
    assert result["end_balance"] == 125000
    assert result["risk_level"] == "LOW"
    assert len(result["timeline"]) == 30


def test_category_breakdown_and_totals():
    purchases = [
        {"name": "Laptop", "category": "Electronics", "amount": 40000,
         "days_from_now": 2},
        {"name": "Phone", "category": "Electronics", "amount": 20000,
         "days_from_now": 5},
        {"name": "Shoes", "category": "Fashion", "amount": 5000,
         "days_from_now": 5},
    ]

    result = analyze_purchases_30_days(base_profile(), purchases)

    assert result["success"] is True
    assert result["total_spend"] == 65000
    assert result["purchases_count"] == 3
    assert result["category_breakdown"][0]["category"] == "Electronics"
    assert result["category_breakdown"][0]["total"] == 60000
    assert result["largest_purchase"]["name"] == "Laptop"


def test_purchases_can_breach_reserve():
    purchases = [
        {"name": "Car", "category": "Vehicle", "amount": 95000,
         "days_from_now": 1},
    ]

    result = analyze_purchases_30_days(base_profile(), purchases)

    assert result["risk_level"] in {"MEDIUM", "HIGH"}
    assert result["days_below_reserve"] > 0
    assert result["minimum_balance"] < result["start_balance"]


def test_purchase_going_negative_is_high_risk():
    profile = base_profile()
    profile["savings"] = 10000
    purchases = [
        {"name": "Emergency", "category": "Other", "amount": 50000,
         "days_from_now": 0},
    ]

    result = analyze_purchases_30_days(profile, purchases)

    assert result["minimum_balance"] < 0
    assert result["risk_level"] == "HIGH"


def test_missing_profile_is_rejected():
    result = analyze_purchases_30_days({"savings": 1000}, [])

    assert result["success"] is False
    assert "monthly_income" in result["missing_fields"]


def test_outside_window_purchase_is_warned():
    purchases = [
        {"name": "Trip", "category": "Travel", "amount": 10000,
         "days_from_now": 45},
    ]

    result = analyze_purchases_30_days(base_profile(), purchases)

    assert result["total_spend"] == 10000
    assert result["warnings"]
