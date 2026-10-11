
import { useEffect, useState, type FormEvent } from "react";
import {
  api,
  type AnalysisResult,
  type Purchase,
  type PurchaseInput,
} from "./api";
import { money } from "./format";
import { BalanceChart, CategoryBars } from "./charts";

const CATEGORIES = [
  "Groceries",
  "Electronics",
  "Fashion",
  "Travel",
  "Health",
  "Education",
  "Home",
  "Vehicle",
  "Entertainment",
  "Bills",
  "Other",
];

const WINDOWS = [
  { days: 7, label: "7 days" },
  { days: 14, label: "14 days" },
  { days: 30, label: "30 days" },
  { days: 60, label: "60 days" },
  { days: 90, label: "90 days" },
];

export function PurchasePlanner() {
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Groceries");
  const [amount, setAmount] = useState("");
  const [daysFromNow, setDaysFromNow] = useState("3");

  const [windowDays, setWindowDays] = useState(30);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  const [loadingList, setLoadingList] = useState(true);
  const [adding, setAdding] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [formError, setFormError] = useState("");
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const data = await api.listPurchases();
        if (active) {
          setPurchases(data);
        }
      } catch (error) {
        if (active) {
          setPageError(
            error instanceof Error ? error.message : "Failed to load purchases."
          );
        }
      } finally {
        if (active) {
          setLoadingList(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    const parsedAmount = Number(amount);
    const parsedDays = Number(daysFromNow);

    if (name.trim() === "") {
      setFormError("Give the purchase a name.");
      return;
    }

    if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      setFormError("Enter a purchase amount greater than zero.");
      return;
    }

    if (!Number.isInteger(parsedDays) || parsedDays < 0 || parsedDays > 365) {
      setFormError("Days from now must be a whole number between 0 and 365.");
      return;
    }

    const payload: PurchaseInput = {
      name: name.trim(),
      category,
      amount: parsedAmount,
      days_from_now: parsedDays,
    };

    setAdding(true);

    try {
      const created = await api.addPurchase(payload);
      setPurchases((previous) =>
        [...previous, created].sort(
          (a, b) => a.days_from_now - b.days_from_now
        )
      );
      setName("");
      setAmount("");
      setDaysFromNow("3");
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Could not add the purchase."
      );
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await api.deletePurchase(id);
      setPurchases((previous) => previous.filter((item) => item.id !== id));
    } catch (error) {
      setPageError(
        error instanceof Error ? error.message : "Could not delete the purchase."
      );
    }
  }

  async function handleAnalyze() {
    setAnalyzing(true);
    setPageError("");

    try {
      setAnalysis(await api.analyze30Days(windowDays));
    } catch (error) {
      setPageError(
        error instanceof Error ? error.message : "Analysis failed."
      );
    } finally {
      setAnalyzing(false);
    }
  }

  const riskClass = analysis?.risk_level
    ? `risk-${analysis.risk_level.toLowerCase()}`
    : "";

  return (
    <div className="panel-stack">
      <section className="hero compact">
        <p className="eyebrow">30-DAY PURCHASE ANALYSIS</p>
        <h2>Plan purchases, see the impact</h2>
        <p>
          Add the purchases you are considering. FinSight projects your daily
          balance, highlights risk days and breaks down spending by category.
        </p>
      </section>

      <section className="card">
        <h3>Add a planned purchase</h3>
        <form className="inline-form" onSubmit={handleAdd}>
          <label className="field grow">
            <span>What is it?</span>
            <input
              type="text"
              value={name}
              placeholder="New laptop"
              onChange={(event) => setName(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Category</span>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              {CATEGORIES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Amount (₹)</span>
            <input
              type="number"
              min="0"
              step="any"
              value={amount}
              placeholder="45000"
              onChange={(event) => setAmount(event.target.value)}
            />
          </label>

          <label className="field">
            <span>In how many days?</span>
            <input
              type="number"
              min="0"
              max="365"
              step="1"
              value={daysFromNow}
              onChange={(event) => setDaysFromNow(event.target.value)}
            />
          </label>

          <button type="submit" className="primary-button" disabled={adding}>
            {adding ? "Adding…" : "Add purchase"}
          </button>
        </form>

        {formError && <p className="error banner">{formError}</p>}
      </section>

      <section className="card">
        <div className="card-head">
          <h3>Planned purchases</h3>
          <span className="pill">{purchases.length} item(s)</span>
        </div>

        {loadingList ? (
          <p className="muted">Loading purchases…</p>
        ) : purchases.length === 0 ? (
          <p className="muted">
            No purchases yet. Add one above to build your plan.
          </p>
        ) : (
          <ul className="purchase-list">
            {purchases.map((purchase) => (
              <li key={purchase.id}>
                <div className="purchase-info">
                  <strong>{purchase.name}</strong>
                  <span className="tag">{purchase.category}</span>
                </div>
                <div className="purchase-meta">
                  <span className="purchase-amount">
                    {money(purchase.amount)}
                  </span>
                  <span className="muted small">
                    {purchase.days_from_now === 0
                      ? "today"
                      : `in ${purchase.days_from_now} day(s)`}
                  </span>
                  <button
                    type="button"
                    className="icon-button"
                    aria-label="Delete purchase"
                    onClick={() => handleDelete(purchase.id)}
                  >
                    ✕
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}

        <div className="analyze-bar">
          <label className="field">
            <span>Analysis window</span>
            <select
              value={windowDays}
              onChange={(event) => setWindowDays(Number(event.target.value))}
            >
              {WINDOWS.map((option) => (
                <option key={option.days} value={option.days}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            className="primary-button"
            disabled={analyzing}
            onClick={handleAnalyze}
          >
            {analyzing ? "Analysing…" : "Run analysis"}
          </button>
        </div>

        {pageError && <p className="error banner">{pageError}</p>}
      </section>

      {analysis && !analysis.success && (
        <section className="card">
          <h3>Profile needed</h3>
          <p>
            Add and assess your financial profile in the Affordability tab
            first — the analysis uses your saved savings, income, expenses,
            debt and reserve.
          </p>
          {analysis.missing_fields && analysis.missing_fields.length > 0 && (
            <p className="warning">
              Missing: {analysis.missing_fields.join(", ")}
            </p>
          )}
        </section>
      )}

      {analysis && analysis.success && (
        <>
          <section className="results-grid">
            <article className="result-card">
              <p>Total planned spend</p>
              <h2>{money(analysis.total_spend ?? 0)}</h2>
              <span>{analysis.purchases_count} purchase(s)</span>
            </article>

            <article className="result-card">
              <p>Projected end balance</p>
              <h2>{money(analysis.end_balance ?? 0)}</h2>
              <span>
                Net cash flow {money(analysis.net_30_day_cash_flow ?? 0)}
              </span>
            </article>

            <article className={`result-card ${riskClass}`}>
              <p>Risk level</p>
              <h2>{analysis.risk_level}</h2>
              <span>
                {analysis.days_below_reserve} day(s) below reserve
              </span>
            </article>
          </section>

          <section className="card">
            <div className="card-head">
              <h3>{analysis.window_days}-day balance projection</h3>
              <span className="pill">
                Lowest {money(analysis.minimum_balance ?? 0)}
              </span>
            </div>
            <BalanceChart
              timeline={analysis.timeline}
              reserve={analysis.emergency_reserve ?? 0}
              startBalance={analysis.start_balance ?? 0}
            />
          </section>

          <div className="split-grid">
            <section className="card">
              <h3>Spending by category</h3>
              <CategoryBars items={analysis.category_breakdown ?? []} />
            </section>

            <section className="card">
              <h3>Weekly summary</h3>
              <div className="week-list">
                {(analysis.weekly_summary ?? []).map((week) => (
                  <div className="week-row" key={week.week}>
                    <span>
                      Week {week.week}
                      <small>
                        {" "}
                        (days {week.day_start}–{week.day_end})
                      </small>
                    </span>
                    <strong>{money(week.closing_balance)}</strong>
                    {week.purchases_total > 0 && (
                      <span className="muted small">
                        −{money(week.purchases_total)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </section>
          </div>

          <section className="card">
            <h3>Recommendation</h3>
            <p className={`recommendation ${riskClass}`}>
              {analysis.recommendation}
            </p>

            <h4>Insights</h4>
            <ul className="insight-list">
              {(analysis.insights ?? []).map((insight) => (
                <li key={insight}>{insight}</li>
              ))}
            </ul>

            {analysis.warnings.length > 0 &&
              analysis.warnings.map((warning) => (
                <p className="warning" key={warning}>
                  ⚠ {warning}
                </p>
              ))}
          </section>
        </>
      )}
    </div>
  );
}
