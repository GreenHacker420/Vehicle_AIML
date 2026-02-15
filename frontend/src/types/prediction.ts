export type ManualPredictionInput = {
  mileage: number;
  engine_hours: number;
  fault_codes: string;
  service_history: string;
  usage_patterns: string;
};

export type PredictionItem = {
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  confidence: number;
  feature_importance: Record<string, number>;
};

export type PredictionResponse = PredictionItem & {
  total_records: number;
  predictions?: PredictionItem[];
  metadata?: Record<string, unknown>;
};
