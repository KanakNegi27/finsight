
const API_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "finsight_token";

export interface User {
  id: number;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Purchase {
  id: number;
  name: string;
  category: string;
  amount: number;
  days_from_now: number;
}

export interface PurchaseInput {
  name: string;
  category: string;
  amount: number;
  days_from_now: number;
}

export interface ProfilePayload {
  savings: number | null;
  monthly_income: number | null;
  monthly_expenses: number | null;
  monthly_debt_payments: number | null;
  purchase_amount: number | null;
  emergency_reserve: number | null;
  historical_expenses: number[];
  field_status: Record<string, string>;
  pending_refund: number | null;
}

export interface AssessmentResult {
  data_quality: {
    data_completeness: number;
    missing_fields: string[];
    invalid_fields: string[];
    estimated_fields: string[];
    warnings: string[];
    is_valid: boolean;
  };
  expense_estimate: {
    estimated: boolean;
    value: number | null;
    range?: { min: number; max: number } | null;
    warnings: string[];
  } | null;
  affordability: {
    recommendation: string;
    confidence: string;
    remaining_savings?: number;
    monthly_surplus?: number;
    warnings: string[];
    missing_fields: string[];
  };
  forecast: {
    success: boolean;
    forecast_days?: number;
    final_balance?: number;
    minimum_projected_balance?: number;
    periods: {
      day_start: number;
      day_end: number;
      closing_balance: number;
      below_reserve: boolean;
    }[];
    warnings: string[];
  };
  warnings: string[];
}

export interface AnalysisTimelineDay {
  day: number;
  opening_balance: number;
  income: number;
  expenses: number;
  debt_payments: number;
  purchases_total: number;
  closing_balance: number;
  below_reserve: boolean;
  purchases: { name: string; category: string; amount: number }[];
}

export interface AnalysisResult {
  success: boolean;
  window_days?: number;
  start_balance?: number;
  emergency_reserve?: number;
  end_balance?: number;
  minimum_balance?: number;
  minimum_balance_day?: number;
  days_below_reserve?: number;
  total_spend?: number;
  purchases_count?: number;
  average_purchase?: number;
  largest_purchase?: { name: string; category: string; amount: number } | null;
  net_30_day_cash_flow?: number;
  discretionary_buffer?: number;
  risk_level?: "LOW" | "MEDIUM" | "HIGH";
  recommendation?: string;
  category_breakdown?: {
    category: string;
    total: number;
    count: number;
    share: number;
  }[];
  weekly_summary?: {
    week: number;
    day_start: number;
    day_end: number;
    purchases_total: number;
    closing_balance: number;
  }[];
  timeline: AnalysisTimelineDay[];
  insights?: string[];
  warnings: string[];
  missing_fields?: string[];
}

let token: string | null = localStorage.getItem(TOKEN_KEY);

export function setToken(value: string | null) {
  token = value;

  if (value) {
    localStorage.setItem(TOKEN_KEY, value);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getToken() {
  return token;
}

function extractError(data: unknown, status: number) {
  const detail = (data as { detail?: unknown } | null)?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => (item as { msg?: string }).msg ?? "Invalid input")
      .join(" ");
  }

  return `Request failed (HTTP ${status})`;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error("Cannot reach the FinSight server. Is it running?");
  }

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new Error(extractError(data, response.status));
  }

  return data as T;
}

export const api = {
  register: (name: string, email: string, password: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/auth/me"),

  getProfile: () => request<ProfilePayload | null>("/profile"),

  saveProfile: (profile: ProfilePayload) =>
    request<ProfilePayload>("/profile", {
      method: "PUT",
      body: JSON.stringify(profile),
    }),

  listPurchases: () => request<Purchase[]>("/purchases"),

  addPurchase: (purchase: PurchaseInput) =>
    request<Purchase>("/purchases", {
      method: "POST",
      body: JSON.stringify(purchase),
    }),

  deletePurchase: (id: number) =>
    request<{ status: string }>(`/purchases/${id}`, { method: "DELETE" }),

  analyze30Days: (days = 30) =>
    request<AnalysisResult>(`/analysis/30-days?days=${days}`),

  assess: (profile: ProfilePayload) =>
    request<AssessmentResult>("/assess", {
      method: "POST",
      body: JSON.stringify(profile),
    }),
};
