
import { useState } from "react";
import { useAuth } from "./auth";
import { AffordabilityPanel } from "./AffordabilityPanel";
import { PurchasePlanner } from "./PurchasePlanner";

type Tab = "affordability" | "analysis";

export function Dashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState<Tab>("affordability");

  const initials = (user?.name ?? "?")
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">₹</span>
          <div className="brand-text">
            <strong>FinSight</strong>
            <small>AI Financial Affordability</small>
          </div>
        </div>

        <nav className="tabs">
          <button
            type="button"
            className={tab === "affordability" ? "tab active" : "tab"}
            onClick={() => setTab("affordability")}
          >
            Affordability
          </button>
          <button
            type="button"
            className={tab === "analysis" ? "tab active" : "tab"}
            onClick={() => setTab("analysis")}
          >
            30-Day Analysis
          </button>
        </nav>

        <div className="user-chip">
          <span className="avatar">{initials}</span>
          <div className="user-details">
            <strong>{user?.name}</strong>
            <small>{user?.email}</small>
          </div>
          <button type="button" className="ghost-button" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="app-main">
        {tab === "affordability" ? <AffordabilityPanel /> : <PurchasePlanner />}
      </main>
    </div>
  );
}
