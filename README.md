# FinSight

> Know what you can truly afford. An AI-powered financial affordability assistant with a 30-day purchase and cash-flow analysis.

FinSight is a full-stack web app that answers a single, practical question: **can I afford this purchase?** It evaluates affordability from savings, income, expenses, debt payments and an emergency reserve — and it still works when some of that data is missing, by estimating intelligently instead of guessing. Signed-in users can save their financial profile, plan upcoming purchases, and get a day-by-day 30-day balance projection with risk scoring and plain-English insights.

---

## Features

- **Smart affordability verdict** — `BUY` / `WAIT` recommendation with a confidence level.
- **Missing-data handling** — estimates unknown monthly expenses from historical totals and clearly flags every estimate.
- **90-day cash-flow forecast** — projects balance over 90 days and warns about reserve breaches.
- **30-day purchase analysis** — day-by-day balance projection, category breakdown, weekly summary, risk level and insights.
- **User accounts** — register / sign in with hashed passwords and signed bearer tokens.
- **Saved profiles & purchases** — data persists per user in SQLite.
- **Modern UI** — gradient design, glass header, tabbed dashboard and animated charts, fully responsive.

---

## Tech Stack

| Layer      | Technology                                  |
| ---------- | ------------------------------------------- |
| Backend    | Python, FastAPI, Pydantic                   |
| Auth       | PBKDF2-HMAC-SHA256 passwords, HMAC-signed tokens (standard library) |
| Database   | SQLite (standard library `sqlite3`)         |
| Frontend   | React 19, TypeScript, Vite                  |
| Charts     | Hand-built SVG + CSS (no chart dependency)  |
| Tests      | pytest                                      |

No external runtime dependencies are required beyond FastAPI/Uvicorn on the backend and React/Vite on the frontend — authentication, tokens and storage all use the Python standard library.

---

## Project Structure

```
AI_financial_affordability/
├── finsight-backend/            # FastAPI + SQLite API
│   ├── main.py                  # App, routes, auth dependency
│   ├── database.py              # SQLite persistence layer
│   ├── schemas.py               # Pydantic request/response models
│   ├── services/
│   │   ├── affordability.py     # BUY/WAIT decision engine
│   │   ├── data_quality.py      # Completeness & validity checks
│   │   ├── estimator.py         # Missing-expense estimation
│   │   ├── forecast.py          # 90-day cash-flow forecast
│   │   ├── analysis.py          # 30-day purchase analysis
│   │   └── auth.py              # Password hashing + tokens
│   └── tests/                   # pytest suite
│
└── finsight/                    # React + TypeScript + Vite frontend
    ├── src/
    │   ├── api.ts               # Typed API client
    │   ├── auth.ts              # Auth context + useAuth hook
    │   ├── AuthProvider.tsx     # Session provider
    │   ├── Login.tsx            # Login / register page
    │   ├── Dashboard.tsx        # App shell + tabs
    │   ├── AffordabilityPanel.tsx
    │   ├── PurchasePlanner.tsx  # Purchases + 30-day analysis
    │   ├── charts.tsx           # SVG balance chart + category bars
    │   ├── App.tsx              # Root + route gate
    │   └── App.css / index.css  # Theme & component styles
    └── package.json
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Backend

```powershell
cd finsight-backend

# create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate       # macOS / Linux

pip install fastapi uvicorn pydantic pytest

# run the API (http://localhost:8000)
python -m uvicorn main:app --reload
```

Interactive API docs are available at <http://localhost:8000/docs>.

The SQLite database (`finsight.db`) is created automatically on startup.

### Frontend

```bash
cd finsight
npm install
npm run dev
```

Open **http://localhost:5173**. Create an account, fill in your financial
profile and press **Assess** (it saves automatically), then open the
**30-Day Analysis** tab to plan purchases.

> The backend must be running on `http://127.0.0.1:8000` for the frontend to
> work. CORS is pre-configured for `localhost:5173`.

---

## Environment Variables

All optional — sensible development defaults are built in.

| Variable | Default | Purpose |
| --- | --- | --- |
| `FINSIGHT_SECRET_KEY` | `finsight-dev-secret-change-me` | Secret used to sign auth tokens. **Set this in production.** |
| `FINSIGHT_TOKEN_TTL` | `604800` (7 days) | Token lifetime in seconds. |
| `FINSIGHT_DB_PATH` | `finsight-backend/finsight.db` | SQLite database file path. |

---

## API Reference

Authenticated endpoints expect an `Authorization: Bearer <token>` header.

| Method | Endpoint | Auth | Description |
| --- | --- | :---: | --- |
| `GET` | `/` | — | Service info |
| `GET` | `/health` | — | Health check |
| `POST` | `/auth/register` | — | Create an account, returns a token |
| `POST` | `/auth/login` | — | Sign in, returns a token |
| `GET` | `/auth/me` | ✅ | Current user |
| `GET` | `/profile` | ✅ | Read the saved financial profile |
| `PUT` | `/profile` | ✅ | Save / update the financial profile |
| `POST` | `/assess` | — | Affordability assessment (verdict, estimate, 90-day forecast) |
| `GET` | `/purchases` | ✅ | List planned purchases |
| `POST` | `/purchases` | ✅ | Add a planned purchase |
| `DELETE` | `/purchases/{id}` | ✅ | Delete a planned purchase |
| `GET` | `/analysis/30-days` | ✅ | 30-day purchase & cash-flow analysis (`?days=7..90`) |

### Example

```bash
# Register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada","email":"ada@example.com","password":"supersecret"}'

# Use the returned token
curl http://127.0.0.1:8000/analysis/30-days \
  -H "Authorization: Bearer <token>"
```

---

## How the 30-Day Analysis Works

1. Monthly income, expenses and debt payments are prorated to a daily rate
   (`/ 30`).
2. The balance starts at your savings; purchases scheduled for *today* are
   applied immediately.
3. For each of the next 30 days the net daily cash flow is applied, then any
   purchases scheduled that day are subtracted.
4. The result includes:
   - **KPIs** — total spend, projected end balance, lowest balance, net cash flow.
   - **Category breakdown** — spend and share per category.
   - **Weekly summary** — closing balance per week.
   - **Risk level** — `LOW` / `MEDIUM` / `HIGH`, based on reserve breaches and cash flow.
   - **Insights** — human-readable explanations and a recommendation.

Anything that falls outside the selected window is reported as a warning and
excluded from the timeline.

---

## Missing-Data Handling

FinSight never silently invents numbers. If monthly expenses are unknown, it
estimates them from at least three historical monthly totals (median) and:

- tags the value as **estimated**,
- reports an observed historical range (not a confidence interval),
- forces the affordability confidence to **LOW**.

Pending refunds are always excluded from available savings and called out in
the warnings.

---

## Testing

From the `finsight-backend` directory:

```bash
.venv\Scripts\python.exe -m pytest -q     # Windows
# python -m pytest -q                      # macOS / Linux
```

The suite covers the affordability engine, data quality, estimation, forecast,
authentication and the 30-day analysis.

Frontend checks (from the `finsight` directory):

```bash
npm run lint      # ESLint
npm run build     # tsc typecheck + production build
```

---

## Notes & Limitations

- The development secret key is **not** safe for production — set `FINSIGHT_SECRET_KEY`.
- Expense estimates and forecasts are indicative, not financial advice.
- SQLite is used for simplicity; swap it for Postgres for multi-user deployments.

---

## License

MIT
