export type ManualPredictionInput = {
  mileage: number;
  engine_hours: number;
  fault_codes: string;
  service_history: string;
  usage_patterns: string;
};

export type PredictionItem = {
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  risk_probability: number;
  confidence: number;
  feature_importance: Record<string, number>;
  insight_summary?: string | null;
  insight_source?: "RULES" | "GENAI_LLM";
  insight_drivers?: InsightDriver[];
  recommendations?: RecommendationItem[];
  data_warnings?: string[];
};

export type InsightDriver = {
  factor: string;
  observed_value: string;
  direction: "RISK_UP" | "RISK_DOWN" | "NEUTRAL";
  impact: number;
  explanation: string;
};

export type RecommendationItem = {
  priority: "HIGH" | "MEDIUM" | "LOW";
  action: string;
  rationale: string;
};

export type PredictionResponse = PredictionItem & {
  total_records: number;
  predictions?: PredictionItem[];
  metadata?: Record<string, unknown>;
};
