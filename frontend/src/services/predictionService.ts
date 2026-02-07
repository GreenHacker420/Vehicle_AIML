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

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        message =
          typeof payload.detail === "string"
            ? payload.detail
            : JSON.stringify(payload.detail);
      }
    } catch {
      // Keep fallback message.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function predictFromManualInput(
  payload: ManualPredictionInput,
): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseResponse<PredictionResponse>(response);
}

export async function predictFromCsvFile(
  file: File,
): Promise<PredictionResponse> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    body: form,
  });

  return parseResponse<PredictionResponse>(response);
}

