const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");
const SESSION_KEY = "trustsentinel.session";

export interface ApiError extends Error {
  status?: number;
  code?: string;
}

export interface SessionUser {
  email: string;
  display_name: string;
  role: "analyst";
}

export interface RiskResult {
  transaction_id: string;
  risk_score: number;
  risk_band: string;
  recommended_action: string;
  rule_score: number;
  ml_score: number | null;
  ml_status: string;
  model_version: string;
  hybrid_policy_version: string;
  feature_schema_version: string;
  reason_codes: string[];
  explanation: string;
  latency_ms: number;
  signals: Array<{
    signal_type: string;
    triggered: boolean;
    severity: number;
    evidence: string;
    source_feature: string;
  }>;
  case_id: string | null;
}

export interface CaseRecord {
  case_id: string;
  transaction_id: string;
  status: string;
  outcome: string | null;
  analyst_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  transaction: { amount: number; currency: string; account_id: string } | null;
  decision: {
    risk_score: number;
    risk_band: string;
    recommended_action: string;
    reason_codes: string[];
    explanation: string;
  } | null;
  signals: Array<{
    signal_type: string;
    source_feature: string;
    signal_value: number;
    evidence: string;
    severity: number;
  }>;
  timeline: Array<{
    actor: string;
    event: string;
    created_at: string;
    metadata: Record<string, unknown>;
  }>;
}

function token() {
  return typeof window === "undefined"
    ? null
    : window.sessionStorage.getItem(SESSION_KEY);
}

export function hasSession() {
  return Boolean(token());
}

export function clearSession() {
  if (typeof window !== "undefined") window.sessionStorage.removeItem(SESSION_KEY);
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  authenticated = true,
): Promise<T> {
  if (!API_BASE_URL) throw new Error("TrustSentinel API URL is not configured.");

  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  const accessToken = authenticated ? token() : null;
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const code = body?.error?.code ?? body?.detail?.error?.code;
      const message = response.status === 500
        ? "TrustSentinel encountered an internal error while processing this request."
        : response.status === 422
          ? "Please check the transaction details and try again."
          : response.status === 401 && authenticated
            ? "Your session has expired. Please sign in again."
            : body?.error?.message ?? body?.detail?.error?.message ??
              (typeof body?.detail === "string" ? body.detail : `Request failed (${response.status}).`);
      const error = new Error(message) as ApiError;
      error.status = response.status;
      error.code = code;
      if (response.status === 401 && authenticated) {
        clearSession();
        window.dispatchEvent(new Event("trustsentinel:session-expired"));
      }
      throw error;
    }
    return body as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("TrustSentinel API request timed out.");
    }
    if (error instanceof TypeError) throw new Error("Unable to connect to TrustSentinel API.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function login(email: string, password: string) {
  const result = await apiFetch<{ access_token: string; expires_in: number }>(
    "/v1/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) },
    false,
  );
  window.sessionStorage.setItem(SESSION_KEY, result.access_token);
  return getSession();
}

export function getSession() {
  return apiFetch<SessionUser>("/v1/auth/session");
}

export async function runScenario(scenario: string) {
  return apiFetch<RiskResult>("/v1/sandbox/scenario", {
    method: "POST",
    body: JSON.stringify({ scenario }),
  });
}

export function scoreTransaction(data: {
  transaction_id: string;
  account_id: string;
  amount: number;
  currency: string;
  beneficiary_id: string;
  device_id: string;
  channel: "mobile_app" | "web" | "ussd" | "api";
}) {
  return apiFetch<RiskResult>("/v1/risk/score", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getHealth() {
  return apiFetch<{ status: string; service: string; version: string }>("/health", {}, false);
}

export function getReady() {
  return apiFetch<{
    status: string;
    database: string;
    ml_status: string;
    model_version: string;
    hybrid_policy_version: string;
  }>("/ready", {}, false);
}

export function getMetrics() {
  return apiFetch<{
    transactions_evaluated: number;
    high_risk_transactions: number;
    high_risk_rate: number;
    warnings: number;
    step_ups: number;
    holds: number;
    reviews: number;
    cases_created: number;
    analyst_actions: number;
    average_latency_ms: number;
  }>("/v1/metrics/summary");
}

export function getTransactions(limit = 100) {
  return apiFetch<{ items: Array<Record<string, unknown>>; count: number }>(
    `/v1/transactions?limit=${limit}`,
  );
}

export function getTransaction(id: string) {
  return apiFetch<Record<string, unknown>>(`/v1/transactions/${encodeURIComponent(id)}`);
}

export function getCases(params?: { status?: string; outcome?: string }) {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.outcome) search.set("outcome", params.outcome);
  const query = search.toString();
  return apiFetch<{ items: CaseRecord[]; count: number }>(`/v1/cases${query ? `?${query}` : ""}`);
}

export function getCase(id: string) {
  return apiFetch<CaseRecord>(`/v1/cases/${encodeURIComponent(id)}`);
}

export function getAuditEvents(limit = 100) {
  return apiFetch<{ items: Array<{
    event: string;
    actor: string;
    entity_type: string;
    entity_id: string;
    metadata: Record<string, unknown>;
    created_at: string;
  }>; count: number }>(`/v1/audit?limit=${limit}`);
}

export function updateCaseOutcome(
  id: string,
  data: {
    outcome: "CONFIRMED_SCAM" | "LEGITIMATE" | "NEEDS_REVIEW" | "ESCALATED";
    notes?: string;
    analyst_id: string;
  },
) {
  return apiFetch<CaseRecord>(`/v1/cases/${encodeURIComponent(id)}/outcome`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
