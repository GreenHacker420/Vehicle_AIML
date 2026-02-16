export type FeatureImportancePair = {
  feature: string;
  value: number;
};

export function toSortedFeatureImportance(
  featureImportance: Record<string, number>,
): FeatureImportancePair[] {
  return Object.entries(featureImportance)
    .map(([feature, value]) => ({ feature, value }))
    .sort((a, b) => b.value - a.value);
}
