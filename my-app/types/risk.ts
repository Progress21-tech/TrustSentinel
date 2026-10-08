export type RiskBand =
  | "LOW"
  | "MODERATE"
  | "ELEVATED"
  | "HIGH"
  | "CRITICAL";

export type InterventionAction =
  | "ALLOW"
  | "WARN"
  | "STEP_UP"
  | "HOLD"
  | "REVIEW";

export interface RiskDecision {
  transactionId: string;
  riskScore: number;
  riskBand: RiskBand;
  recommendedAction: InterventionAction;
  reasonCodes: string[];
  explanation: string;
  modelVersion: string;
  latencyMs: number;
}

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  amount: number;
  accountAgeDays: number;
  beneficiaryFirstSeenDays: number;
  recentDeviceChange: boolean;
  transactionVelocity30m: number;
  decision: RiskDecision;
}