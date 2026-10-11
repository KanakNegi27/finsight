
from services.estimator import estimate_missing_expenses


def test_estimate_from_history():
    profile = {"monthly_expenses": None}

    result = estimate_missing_expenses(
        profile,
        [14000, 16000, 15000, 18000, 15500],
    )

    assert result["estimated"] is True
    assert result["value"] == 15500
    assert result["range"]["min"] == 14000
    assert result["range"]["max"] == 18000


def test_insufficient_history():
    profile = {"monthly_expenses": None}

    result = estimate_missing_expenses(
        profile,
        [14000, 16000],
    )

    assert result["estimated"] is False
    assert result["value"] is None
    assert result["range"] is None


def test_no_history():
    profile = {"monthly_expenses": None}

    result = estimate_missing_expenses(profile)

    assert result["estimated"] is False
    assert result["value"] is None


def test_existing_expenses_are_preserved():
    profile = {"monthly_expenses": 17000}

    result = estimate_missing_expenses(
        profile,
        [14000, 16000, 15000],
    )

    assert result["estimated"] is False
    assert result["value"] == 17000


def test_invalid_history_values_are_ignored():
    profile = {"monthly_expenses": None}

    result = estimate_missing_expenses(
        profile,
        [10000, "invalid", -500, 12000, 11000],
    )

    assert result["estimated"] is True
    assert result["value"] == 11000
    assert result["historical_months_used"] == 3
