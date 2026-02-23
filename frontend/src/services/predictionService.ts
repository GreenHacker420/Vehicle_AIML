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
  (typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? "https://vehicle-aiml-backend.vercel.app"
    : "http://localhost:8000");

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        if (Array.isArray(payload.detail)) {
          const parts = payload.detail.map((item: unknown) => {
            if (typeof item === "string") {
              return item;
            }
            if (
              item &&
              typeof item === "object" &&
              "msg" in item &&
              typeof (item as { msg: unknown }).msg === "string"
            ) {
              return (item as { msg: string }).msg;
            }
            return JSON.stringify(item);
          });
          message = parts.join(" | ");
        } else if (typeof payload.detail === "string") {
          message = payload.detail;
        } else {
          message = JSON.stringify(payload.detail);
        }
      }
    } catch {
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function predictFromManualInput(
  payload: ManualPredictionInput,
): Promise<PredictionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    return parseResponse<PredictionResponse>(response);
  } catch {
    throw new Error(
      "Unable to reach prediction API. Check your connection or backend status.",
    );
  }
}

export async function predictFromCsvFile(
  file: File,
): Promise<PredictionResponse> {
  const form = new FormData();
  form.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      body: form,
    });
    return parseResponse<PredictionResponse>(response);
  } catch {
    throw new Error(
      "Unable to reach prediction API. Check your connection or backend status.",
    );
  }
}
