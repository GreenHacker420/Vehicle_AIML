export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export function riskBadgeClass(riskLevel: RiskLevel): string {
  if (riskLevel === "LOW") return "text-emerald-700 bg-emerald-100";
  if (riskLevel === "MEDIUM") return "text-amber-700 bg-amber-100";
  return "text-red-700 bg-red-100";
}

export function riskLevelOrder(riskLevel: RiskLevel): number {
  if (riskLevel === "LOW") return 0;
  if (riskLevel === "MEDIUM") return 1;
  return 2;
}
