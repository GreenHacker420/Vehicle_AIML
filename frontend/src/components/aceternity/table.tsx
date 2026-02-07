import { cn } from "@/lib/utils";

type FeatureTableProps = {
  rows: Array<{ feature: string; importance: number }>;
  className?: string;
};

export function AceternityFeatureTable({ rows, className }: FeatureTableProps) {
  if (rows.length === 0) {
    return (
      <div
        className={cn(
          "rounded-2xl border border-white/10 bg-slate-900/40 px-4 py-3 text-sm text-slate-300",
          className,
        )}
      >
        No feature importance values returned.
      </div>
    );
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-white/10 bg-slate-900/40",
        className,
      )}
    >
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-slate-900/90 text-xs uppercase tracking-wider text-slate-300">
          <tr>
            <th className="px-4 py-3 font-medium">Feature</th>
            <th className="px-4 py-3 text-right font-medium">Importance</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.feature}
              className="border-t border-white/10 text-slate-100 transition hover:bg-slate-800/30"
            >
              <td className="px-4 py-2.5 capitalize">
                {row.feature.replace(/_/g, " ")}
              </td>
              <td className="px-4 py-2.5 text-right tabular-nums">
                {(row.importance * 100).toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

