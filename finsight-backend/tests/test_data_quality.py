
from services.data_quality import check_data_quality


def test_complete_profile():
    profile = {
        "savings": 50000,
        "monthly_income": 30000,
        "monthly_expenses": 15000,
        "monthly_debt_payments": 2000,
        "purchase_amount": 10000,
        "emergency_reserve": 15000,
    }

    result = check_data_quality(profile)

    assert result["data_completeness"] == 1.0
    assert result["is_valid"] is True
    assert result["missing_fields"] == []


def test_missing_income():
    profile = {
        "savings": 50000,
        "monthly_income": None,
        "monthly_expenses": 15000,
        "monthly_debt_payments": 2000,
        "purchase_amount": 10000,
        "emergency_reserve": 15000,
    }

    result = check_data_quality(profile)

    assert result["data_completeness"] < 1.0
    assert "monthly_income" in result["missing_fields"]
    assert result["is_valid"] is False


def test_negative_value():
    profile = {
        "savings": -500,
        "monthly_income": 30000,
        "monthly_expenses": 15000,
        "monthly_debt_payments": 2000,
        "purchase_amount": 10000,
        "emergency_reserve": 15000,
    }

    result = check_data_quality(profile)

    assert "savings" in result["invalid_fields"]
    assert result["is_valid"] is False


def test_estimated_expenses():
    profile = {
        "savings": 50000,
        "monthly_income": 30000,
        "monthly_expenses": 15000,
        "monthly_debt_payments": 2000,
        "purchase_amount": 10000,
        "emergency_reserve": 15000,
        "field_status": {
            "monthly_expenses": "estimated"
        },
    }

    result = check_data_quality(profile)

    assert "monthly_expenses" in result["estimated_fields"]
    assert result["warnings"]
