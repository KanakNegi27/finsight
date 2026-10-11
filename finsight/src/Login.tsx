
import { useState, type FormEvent } from "react";
import { useAuth } from "./auth";

type Mode = "login" | "register";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

interface FieldErrors {
  name?: string;
  email?: string;
  password?: string;
  confirm?: string;
}

export function Login() {
  const { login, register } = useAuth();

  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [loading, setLoading] = useState(false);

  function switchMode(next: Mode) {
    setMode(next);
    setErrors({});
    setFormError("");
  }

  function validate(): boolean {
    const next: FieldErrors = {};

    if (mode === "register" && name.trim().length < 2) {
      next.name = "Please enter your name (at least 2 characters).";
    }

    if (!EMAIL_RE.test(email.trim())) {
      next.email = "Please enter a valid email address.";
    }

    if (mode === "register" && password.length < 8) {
      next.password = "Password must be at least 8 characters.";
    } else if (mode === "login" && password.length === 0) {
      next.password = "Please enter your password.";
    }

    if (mode === "register" && confirm !== password) {
      next.confirm = "Passwords do not match.";
    }

    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    if (!validate()) {
      return;
    }

    setLoading(true);

    try {
      if (mode === "login") {
        await login(email.trim(), password);
      } else {
        await register(name.trim(), email.trim(), password);
      }
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <aside className="auth-brand">
        <div className="brand-mark large">₹</div>
        <h1>FinSight</h1>
        <p className="auth-tagline">
          Decide with confidence. Know what you can truly afford before you
          spend.
        </p>

        <ul className="auth-features">
          <li>
            <span className="feature-dot" />
            Handles missing financial data intelligently
          </li>
          <li>
            <span className="feature-dot" />
            30-day purchase and cash-flow analysis
          </li>
          <li>
            <span className="feature-dot" />
            Personal dashboard saved to your account
          </li>
        </ul>

        <div className="auth-glow" />
      </aside>

      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-tabs">
            <button
              type="button"
              className={mode === "login" ? "auth-tab active" : "auth-tab"}
              onClick={() => switchMode("login")}
            >
              Sign in
            </button>
            <button
              type="button"
              className={mode === "register" ? "auth-tab active" : "auth-tab"}
              onClick={() => switchMode("register")}
            >
              Create account
            </button>
          </div>

          <h2>
            {mode === "login" ? "Welcome back" : "Get started"}
          </h2>
          <p className="auth-subtitle">
            {mode === "login"
              ? "Sign in to open your financial dashboard."
              : "Create an account to save your profile and analysis."}
          </p>

          <form onSubmit={handleSubmit} noValidate>
            {mode === "register" && (
              <label className="field">
                <span>Full name</span>
                <input
                  type="text"
                  value={name}
                  autoComplete="name"
                  placeholder="Ada Lovelace"
                  className={errors.name ? "invalid" : ""}
                  onChange={(event) => setName(event.target.value)}
                />
                {errors.name && <small className="field-error">{errors.name}</small>}
              </label>
            )}

            <label className="field">
              <span>Email</span>
              <input
                type="email"
                value={email}
                autoComplete="email"
                placeholder="you@example.com"
                className={errors.email ? "invalid" : ""}
                onChange={(event) => setEmail(event.target.value)}
              />
              {errors.email && <small className="field-error">{errors.email}</small>}
            </label>

            <label className="field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                placeholder="••••••••"
                className={errors.password ? "invalid" : ""}
                onChange={(event) => setPassword(event.target.value)}
              />
              {errors.password && (
                <small className="field-error">{errors.password}</small>
              )}
            </label>

            {mode === "register" && (
              <label className="field">
                <span>Confirm password</span>
                <input
                  type="password"
                  value={confirm}
                  autoComplete="new-password"
                  placeholder="••••••••"
                  className={errors.confirm ? "invalid" : ""}
                  onChange={(event) => setConfirm(event.target.value)}
                />
                {errors.confirm && (
                  <small className="field-error">{errors.confirm}</small>
                )}
              </label>
            )}

            {formError && <p className="error banner">{formError}</p>}

            <button type="submit" className="primary-button" disabled={loading}>
              {loading
                ? "Please wait…"
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
