
from services.affordability import assess_affordability


def test_affordable_purchase():
    profile = {
        "savings": 100000,
        "monthly_income": 50000,
        "monthly_expenses": 20000,
        "monthly_debt_payments": 5000,
        "purchase_amount": 10000,
        "emergency_reserve": 20000,
    }

    result = assess_affordability(profile)

    assert result["recommendation"] == "BUY"


def test_unaffordable_purchase():
    profile = {
        "savings": 30000,
        "monthly_income": 30000,
        "monthly_expenses": 20000,
        "monthly_debt_payments": 5000,
        "purchase_amount": 25000,
        "emergency_reserve": 15000,
    }

    result = assess_affordability(profile)

    assert result["recommendation"] == "WAIT"
