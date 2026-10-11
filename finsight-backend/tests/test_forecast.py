
from services.forecast import forecast_cash_flow


def sample_profile():
    return {
        "savings": 100000,
        "monthly_income": 50000,
        "monthly_expenses": 20000,
        "monthly_debt_payments": 5000,
        "purchase_amount": 10000,
        "emergency_reserve": 20000,
    }


def test_90_day_forecast():
    result = forecast_cash_flow(sample_profile())

    assert result["success"] is True
    assert result["forecast_days"] == 90
    assert len(result["periods"]) == 3
    assert result["final_balance"] == 165000


def test_missing_income_blocks_forecast():
    profile = sample_profile()
    profile["monthly_income"] = None

    result = forecast_cash_flow(profile)

    assert result["success"] is False
    assert "monthly_income" in result["missing_fields"]
    assert result["periods"] == []


def test_purchase_breaches_reserve():
    profile = sample_profile()
    profile["purchase_amount"] = 90000

    result = forecast_cash_flow(profile)

    assert result["success"] is True
    assert result["minimum_projected_balance"] == 10000
    assert result["warnings"]


def test_invalid_forecast_days():
    result = forecast_cash_flow(sample_profile(), days=0)

    assert result["success"] is False


def test_negative_financial_value():
    profile = sample_profile()
    profile["savings"] = -100

    result = forecast_cash_flow(profile)

    assert result["success"] is False
