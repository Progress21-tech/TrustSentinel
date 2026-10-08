const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

async function apiFetch(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const body = await response.json();
      message =
        body?.error?.message ||
        body?.detail?.error?.message ||
        body?.detail ||
        message;
    } catch {
      // Keep the default message.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function runScenario(scenario: string) {
  return apiFetch("/v1/sandbox/scenario", {
    method: "POST",
    body: JSON.stringify({ scenario }),
  });
}

export async function getHealth() {
  return apiFetch("/health");
}

export async function getReady() {
  return apiFetch("/ready");
}

export async function getMetrics() {
  return apiFetch("/v1/metrics/summary");
}

export async function getTransaction(id: string) {
  return apiFetch(`/v1/transactions/${encodeURIComponent(id)}`);
}

export async function getCases(params?: {
  status?: string;
  risk_band?: string;
  outcome?: string;
}) {
  const search = new URLSearchParams();

  if (params?.status) search.set("status", params.status);
  if (params?.risk_band) search.set("risk_band", params.risk_band);
  if (params?.outcome) search.set("outcome", params.outcome);

  const query = search.toString();

  return apiFetch(`/v1/cases${query ? `?${query}` : ""}`);
}

export async function getCase(id: string) {
  return apiFetch(`/v1/cases/${encodeURIComponent(id)}`);
}

export async function updateCaseOutcome(
  id: string,
  data: {
    outcome: "CONFIRMED_SCAM" | "LEGITIMATE" | "NEEDS_REVIEW" | "ESCALATED";
    notes?: string;
    analyst_id?: string;
  }
) {
  return apiFetch(`/v1/cases/${encodeURIComponent(id)}/outcome`, {
    method: "POST",
    body: JSON.stringify({
      analyst_id: "sandbox-analyst",
      ...data,
    }),
  });
}