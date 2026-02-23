import type {
  ManualPredictionInput,
  PredictionResponse,
} from "@/types/prediction";

export type {
  InsightDriver,
  ManualPredictionInput,
  PredictionItem,
  PredictionResponse,
  RecommendationItem,
} from "@/types/prediction";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");

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
