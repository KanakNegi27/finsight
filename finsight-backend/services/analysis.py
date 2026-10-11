"""30-day purchase analysis.

Projects the day-by-day cash balance over the next 30 days while taking
scheduled purchases into account, then summarises spending, risk and
actionable insights.
"""

from __future__ import annotations

from collections import defaultdict

WINDOW_DAYS = 30
DAYS_PER_MONTH = 30


def _round(value: float) -> float:
    return round(value, 2)


def analyze_purchases_30_days(
    profile: dict,
    purchases: list[dict] | None = None,
    days: int = WINDOW_DAYS,
) -> dict:
    purchases = purchases or []

    required_fields = [
        "savings",
        "monthly_income",
        "monthly_expenses",
        "monthly_debt_payments",
        "emergency_reserve",
    ]

    missing = [f for f in required_fields if profile.get(f) is None]
    if missing:
        return {
            "success": False,
            "missing_fields": missing,
            "warnings": [
                "Provide savings, income, expenses, debt and reserve "
                "before analysing purchases."
            ],
            "timeline": [],
            "insights": [],
        }

    try:
        savings = float(profile["savings"])
        income = float(profile["monthly_income"])
        expenses = float(profile["monthly_expenses"])
        debt = float(profile["monthly_debt_payments"])
        reserve = float(profile["emergency_reserve"])
    except (TypeError, ValueError):
        return {
            "success": False,
            "missing_fields": [],
            "warnings": ["Financial values must be valid numbers."],
            "timeline": [],
            "insights": [],
        }

    if min(savings, income, expenses, debt, reserve) < 0:
        return {
            "success": False,
            "missing_fields": [],
            "warnings": ["Financial values cannot be negative."],
            "timeline": [],
            "insights": [],
        }

    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        return {
            "success": False,
            "missing_fields": [],
            "warnings": ["Analysis window must be a positive integer."],
            "timeline": [],
            "insights": [],
        }

    # Normalise purchases and validate amounts.
    scheduled: dict[int, list[dict]] = defaultdict(list)
    outside_window = []
    total_spend = 0.0
    warnings = []

    for item in purchases:
        if isinstance(item, bool) or not isinstance(item, dict):
            continue

        try:
            amount = float(item.get("amount"))
        except (TypeError, ValueError):
            continue

        if amount <= 0:
            continue

        offset = item.get("days_from_now", 0)
        try:
            offset = int(offset)
        except (TypeError, ValueError):
            offset = 0

        entry = {
            "name": item.get("name") or "Purchase",
            "category": item.get("category") or "Other",
            "amount": amount,
            "days_from_now": offset,
        }

        if offset <= 0:
            scheduled[0].append(entry)
        elif offset <= days:
            scheduled[offset].append(entry)
        else:
            outside_window.append(entry)

        total_spend += amount

    daily_income = income / DAYS_PER_MONTH
    daily_expenses = expenses / DAYS_PER_MONTH
    daily_debt = debt / DAYS_PER_MONTH

    balance = savings
    timeline = []
    category_totals: dict[str, float] = defaultdict(float)
    category_counts: dict[str, int] = defaultdict(int)

    # Purchases happening today reduce the opening balance immediately.
    today_total = sum(p["amount"] for p in scheduled.get(0, []))
    balance -= today_total

    for entry in scheduled.get(0, []):
        category_totals[entry["category"]] += entry["amount"]
        category_counts[entry["category"]] += 1

    minimum_balance = balance
    minimum_balance_day = 0
    days_below_reserve = 1 if balance < reserve else 0

    for day in range(1, days + 1):
        opening = balance
        balance += daily_income - daily_expenses - daily_debt

        day_purchases = scheduled.get(day, [])
        purchase_total = 0.0
        for entry in day_purchases:
            purchase_total += entry["amount"]
            category_totals[entry["category"]] += entry["amount"]
            category_counts[entry["category"]] += 1

        balance -= purchase_total

        below_reserve = balance < reserve
        if below_reserve:
            days_below_reserve += 1

        if balance < minimum_balance:
            minimum_balance = balance
            minimum_balance_day = day

        timeline.append({
            "day": day,
            "opening_balance": _round(opening),
            "income": _round(daily_income),
            "expenses": _round(daily_expenses),
            "debt_payments": _round(daily_debt),
            "purchases_total": _round(purchase_total),
            "closing_balance": _round(balance),
            "below_reserve": below_reserve,
            "purchases": [
                {
                    "name": entry["name"],
                    "category": entry["category"],
                    "amount": _round(entry["amount"]),
                }
                for entry in day_purchases
            ],
        })

    end_balance = _round(balance)
    net_cash_flow = _round(income - expenses - debt)
    discretionary_buffer = _round(end_balance - reserve)

    # Category breakdown sorted by spend.
    category_breakdown = [
        {
            "category": category,
            "total": _round(total),
            "count": category_counts[category],
            "share": _round(total / total_spend * 100) if total_spend else 0.0,
        }
        for category, total in sorted(
            category_totals.items(),
            key=lambda pair: pair[1],
            reverse=True,
        )
    ]

    # Weekly summary (up to 4 weeks in a 30-day window).
    weekly_summary = []
    for week_index, start in enumerate(range(1, days + 1, 7)):
        week_days = timeline[start - 1:start + 6]
        if not week_days:
            continue
        weekly_summary.append({
            "week": week_index + 1,
            "day_start": start,
            "day_end": week_days[-1]["day"],
            "purchases_total": _round(
                sum(d["purchases_total"] for d in week_days)
            ),
            "closing_balance": week_days[-1]["closing_balance"],
        })

    largest = None
    if total_spend:
        all_entries = [
            entry
            for entries in scheduled.values()
            for entry in entries
        ]
        if all_entries:
            biggest = max(all_entries, key=lambda e: e["amount"])
            largest = {
                "name": biggest["name"],
                "category": biggest["category"],
                "amount": _round(biggest["amount"]),
            }

    risk_level = _risk_level(
        minimum_balance, reserve, days_below_reserve, net_cash_flow
    )
    recommendation = _recommendation(risk_level, net_cash_flow)
    insights = _build_insights(
        total_spend,
        net_cash_flow,
        minimum_balance,
        reserve,
        days_below_reserve,
        discretionary_buffer,
        category_breakdown,
        largest,
        purchases_count=sum(category_counts.values()),
    )

    if outside_window:
        warnings.append(
            f"{len(outside_window)} purchase(s) fall outside the "
            f"{days}-day window and were excluded from the timeline."
        )

    return {
        "success": True,
        "window_days": days,
        "start_balance": _round(savings),
        "emergency_reserve": _round(reserve),
        "end_balance": end_balance,
        "minimum_balance": _round(minimum_balance),
        "minimum_balance_day": minimum_balance_day,
        "days_below_reserve": days_below_reserve,
        "total_spend": _round(total_spend),
        "purchases_count": sum(category_counts.values()),
        "average_purchase": _round(
            total_spend / sum(category_counts.values())
        ) if category_counts else 0.0,
        "largest_purchase": largest,
        "net_30_day_cash_flow": net_cash_flow,
        "discretionary_buffer": discretionary_buffer,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "category_breakdown": category_breakdown,
        "weekly_summary": weekly_summary,
        "timeline": timeline,
        "insights": insights,
        "warnings": warnings,
    }


def _risk_level(
    minimum_balance: float,
    reserve: float,
    days_below_reserve: int,
    net_cash_flow: float,
) -> str:
    if minimum_balance < 0 or days_below_reserve >= 10 or net_cash_flow < 0:
        return "HIGH"
    if minimum_balance < reserve or days_below_reserve > 0:
        return "MEDIUM"
    return "LOW"


def _recommendation(risk_level: str, net_cash_flow: float) -> str:
    if risk_level == "HIGH":
        return (
            "HIGH RISK - delay or reduce these purchases; the plan "
            "breaches your reserve."
        )
    if risk_level == "MEDIUM":
        return (
            "PROCEED WITH CARE - the plan stays close to your reserve. "
            "Keep a buffer."
        )
    if net_cash_flow <= 0:
        return (
            "STABLE - purchases fit, but monthly cash flow is neutral. "
            "Avoid new recurring costs."
        )
    return "SAFE - these purchases fit comfortably within your finances."


def _build_insights(
    total_spend: float,
    net_cash_flow: float,
    minimum_balance: float,
    reserve: float,
    days_below_reserve: int,
    discretionary_buffer: float,
    category_breakdown: list[dict],
    largest: dict | None,
    purchases_count: int,
) -> list[str]:
    insights = []

    if purchases_count == 0:
        insights.append(
            "No purchases scheduled in the next 30 days. "
            "Projected balance grows by "
            f"{_round(net_cash_flow)} this month."
        )
        return insights

    insights.append(
        f"You plan {purchases_count} purchase(s) totalling "
        f"{_round(total_spend)} over 30 days."
    )

    if category_breakdown:
        top = category_breakdown[0]
        insights.append(
            f"Biggest category is {top['category']} at {top['total']} "
            f"({top['share']}% of spend)."
        )

    if largest:
        insights.append(
            f"Largest single purchase: {largest['name']} at "
            f"{largest['amount']}."
        )

    if days_below_reserve:
        insights.append(
            f"Balance falls below your {_round(reserve)} reserve on "
            f"{days_below_reserve} day(s) in the window."
        )
    else:
        insights.append(
            "Balance stays above your emergency reserve every day in "
            "the window."
        )

    if minimum_balance < 0:
        insights.append(
            "Warning: the projected balance goes negative - you would "
            "need to borrow or sell an asset."
        )

    if discretionary_buffer > 0:
        insights.append(
            f"You end the month with {discretionary_buffer} of buffer "
            "above your reserve."
        )
    else:
        insights.append(
            f"You end the month {abs(discretionary_buffer)} below your "
            "target reserve."
        )

    return insights
