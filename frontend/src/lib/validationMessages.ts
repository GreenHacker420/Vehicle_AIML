export const validationMessages = {
  mileage: "Mileage is required and must be a non-negative number.",
  engine_hours: "Engine hours are required and must be a non-negative number.",
  fault_codes: "Fault codes are required. Use comma, semicolon, or pipe separators.",
  service_history: "Service history is required (good, average, or poor).",
  usage_patterns: "Usage patterns are required to estimate maintenance risk.",
} as const;

export type ValidationMessageKey = keyof typeof validationMessages;
