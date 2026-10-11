
import { useState, type FormEvent } from "react";
import { api, type AssessmentResult, type ProfilePayload } from "./api";
import { money } from "./format";

export function AffordabilityPanel() {
  const [savings, setSavings] = useState("100000");
  const [income, setIncome] = useState("50000");
  const [expenses, setExpenses] = useState("20000");
  const [debt, setDebt] = useState("5000");
  const [purchase, setPurchase] = useState("10000");
  const [reserve, setReserve] = useState("20000");
  const [refund, setRefund] = useState("25000");

  const [incomeUnknown, setIncomeUnknown] = useState(false);
  const [expensesUnknown, setExpensesUnknown] = useState(false);
  const [refundPending, setRefundPending] = useState(true);

  const [history, setHistory] = useState(["", "", ""]);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [savedProfile, setSavedProfile] = useState(false);

  const fields = [
    { label: "Current savings (₹)", value: savings, set: setSavings, required: true },
    {
      label: "Monthly income (₹)",
      value: income,
      set: setIncome,
      required: !incomeUnknown,
    },
    {
      label: "Monthly expenses (₹)",
      value: expenses,
      set: setExpenses,
      required: !expensesUnknown,
    },
    {
      label: "Monthly debt payments (₹)",
      value: debt,
      set: setDebt,
      required: true,
    },
    { label: "Purchase price (₹)", value: purchase, set: setPurchase, required: true },
    {
      label: "Emergency reserve (₹)",
      value: reserve,
      set: setReserve,
      required: true,
    },
    {
      label: "Expected refund (₹)",
      value: refund,
      set: setRefund,
      required: refundPending,
    },
  ];

  function buildProfile(): ProfilePayload {
    const historicalExpenses = history
      .filter((value) => value.trim() !== "")
      .map(Number);

    return {
      savings: Number(savings),
      monthly_income: incomeUnknown ? null : Number(income),
      monthly_expenses: expensesUnknown ? null : Number(expenses),
      monthly_debt_payments: Number(debt),
      purchase_amount: Number(purchase),
      emergency_reserve: Number(reserve),
      historical_expenses: historicalExpenses,
      field_status: {
        ...(incomeUnknown ? {} : { monthly_income: "confirmed" }),
        ...(expensesUnknown && historicalExpenses.length >= 3
          ? { monthly_expenses: "estimated" }
          : {}),
      },
      pending_refund: refundPending ? Number(refund) : null,
    };
  }

  async function handleAssess(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    setSavedProfile(false);

    const requiredValues = fields.filter((field) => field.required);

    for (const field of requiredValues) {
      const value = Number(field.value);

      if (field.value.trim() === "" || !Number.isFinite(value) || value < 0) {
        setError(
          `Please enter a valid non-negative amount for ${field.label}.`
        );
        return;
      }
    }

    const historicalExpenses = history
      .filter((value) => value.trim() !== "")
      .map(Number);

    if (
      historicalExpenses.some((value) => !Number.isFinite(value) || value < 0)
    ) {
      setError("Historical expenses must be valid non-negative amounts.");
      return;
    }

    setLoading(true);

    try {
      const payload = buildProfile();
      const data = await api.assess(payload);
      setResult(data);

      try {
        await api.saveProfile(payload);
        setSavedProfile(true);
      } catch {
        setSavedProfile(false);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message}. Check that the FastAPI server is running.`
          : "Unable to connect to FinSight."
      );
    } finally {
      setLoading(false);
    }
  }

  const recommendation = result?.affordability.recommendation ?? "";
  const verdictClass =
    recommendation === "BUY"
      ? "verdict buy"
      : recommendation === "WAIT"
        ? "verdict wait"
        : "verdict";

  return (
    <div className="panel-stack">
      <section className="hero">
        <p className="eyebrow">SMARTER FINANCIAL DECISIONS</p>
        <h2>Can you afford your next purchase?</h2>
        <p>
          Assess affordability even when some financial information is
          unavailable. FinSight identifies missing data, estimates what it can,
          and explains its limitations.
        </p>
      </section>

      <form className="card" onSubmit={handleAssess}>
        <h3>Your financial information</h3>

        <div className="form-grid">
          {fields.map((field) => {
            const disabled =
              (field.label.startsWith("Monthly income") && incomeUnknown) ||
              (field.label.startsWith("Monthly expenses") && expensesUnknown) ||
              (field.label.startsWith("Expected refund") && !refundPending);

            return (
              <label className="field" key={field.label}>
                <span>{field.label}</span>
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={field.value}
                  disabled={disabled}
                  required={field.required}
                  onChange={(event) => field.set(event.target.value)}
                />
              </label>
            );
          })}
        </div>

        <div className="unknown-options">
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={incomeUnknown}
              onChange={(event) => setIncomeUnknown(event.target.checked)}
            />
            I don't know my exact monthly income
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={expensesUnknown}
              onChange={(event) => setExpensesUnknown(event.target.checked)}
            />
            I don't know my exact monthly expenses
          </label>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={refundPending}
              onChange={(event) => setRefundPending(event.target.checked)}
            />
            My tax refund is pending and has not been received
          </label>
        </div>

        {expensesUnknown && (
          <section className="history-section">
            <h4>Historical monthly expenses (₹)</h4>
            <p>
              Enter previous monthly totals if available. At least three valid
              values are required for the current estimator.
            </p>

            <div className="form-grid">
              {history.map((value, index) => (
                <label className="field" key={index}>
                  <span>Month {index + 1}</span>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    placeholder="Enter monthly total"
                    value={value}
                    onChange={(event) =>
                      setHistory((previous) =>
                        previous.map((item, i) =>
                          i === index ? event.target.value : item
                        )
                      )
                    }
                  />
                </label>
              ))}
            </div>

            <button
              type="button"
              className="ghost-button"
              onClick={() => setHistory((previous) => [...previous, ""])}
            >
              + Add another month
            </button>
          </section>
        )}

        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Assessing finances…" : "Assess affordability"}
        </button>

        {savedProfile && (
          <p className="success-note">
            ✓ Profile saved to your account — open the 30-Day Analysis tab.
          </p>
        )}

        {error && <p className="error banner">{error}</p>}
      </form>

      {result && (
        <>
          <section className="results-grid">
            <article className={`result-card ${verdictClass}`}>
              <p>Recommendation</p>
              <h2>{recommendation.replaceAll("_", " ")}</h2>
              <span>Confidence: {result.affordability.confidence}</span>
            </article>

            <article className="result-card">
              <p>Remaining savings after purchase</p>
              <h2>
                {result.affordability.remaining_savings == null
                  ? "Unavailable"
                  : money(result.affordability.remaining_savings)}
              </h2>
            </article>

            <article className="result-card">
              <p>Projected balance after 90 days</p>
              <h2>
                {result.forecast.success && result.forecast.final_balance != null
                  ? money(result.forecast.final_balance)
                  : "Unavailable"}
              </h2>
            </article>
          </section>

          {result.expense_estimate?.estimated && (
            <section className="card">
              <h3>Estimated expenses</h3>
              <p>
                Estimated monthly expenses:{" "}
                {result.expense_estimate.value == null
                  ? "Unavailable"
                  : money(result.expense_estimate.value)}
              </p>
              {result.expense_estimate.range && (
                <p>
                  Observed historical range:{" "}
                  {money(result.expense_estimate.range.min)} –{" "}
                  {money(result.expense_estimate.range.max)}
                </p>
              )}
              <p className="warning">
                This is a historical estimate, not a confirmed expense amount.
              </p>
            </section>
          )}

          <section className="card">
            <h3>Data quality</h3>
            <p>
              Completeness:{" "}
              {Math.round(result.data_quality.data_completeness * 100)}%
            </p>

            {result.data_quality.missing_fields.length > 0 && (
              <p>
                Missing information:{" "}
                {result.data_quality.missing_fields.join(", ")}
              </p>
            )}

            <h4>Warnings and limitations</h4>
            {[
              ...result.warnings,
              ...result.data_quality.warnings,
              ...result.affordability.warnings,
              ...result.forecast.warnings,
              ...(result.expense_estimate?.warnings ?? []),
            ]
              .filter((warning, index, all) => all.indexOf(warning) === index)
              .map((warning, index) => (
                <p className="warning" key={`${index}-${warning}`}>
                  ⚠ {warning}
                </p>
              ))}

            {result.forecast.success && (
              <>
                <h4>90-day cash-flow forecast</h4>
                {result.forecast.periods.map((period) => (
                  <div className="forecast-row" key={period.day_start}>
                    <span>
                      Days {period.day_start}–{period.day_end}
                    </span>
                    <strong>{money(period.closing_balance)}</strong>
                    {period.below_reserve && (
                      <span className="error">Below reserve</span>
                    )}
                  </div>
                ))}
              </>
            )}
          </section>
        </>
      )}
    </div>
  );
}
