import type { AnalysisResult } from "../types/analysis";
import { formatPercent } from "../lib/format";
import { riskToneByKey } from "../lib/risk";

type VerdictHeroProps = {
  result: AnalysisResult;
};

export function VerdictHero({ result }: VerdictHeroProps) {
  return (
    <section className="grid gap-3 md:grid-cols-3" aria-label="Analysis summary">
      <article className={`rounded-2xl border bg-forensic-panel/80 p-4 backdrop-blur ${riskToneByKey[result.risk_level]}`}>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Final verdict</p>
        <p className="mt-2 text-2xl font-bold">{result.verdict}</p>
      </article>
      <article className="rounded-2xl border border-forensic-border bg-forensic-panel/80 p-4 backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Confidence</p>
        <p className="mt-2 text-2xl font-bold text-white">{formatPercent(result.confidence_score)}</p>
      </article>
      <article className={`rounded-2xl border bg-forensic-panel/80 p-4 backdrop-blur ${riskToneByKey[result.risk_level]}`}>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Flagged frames</p>
        <p className="mt-2 text-2xl font-bold">{result.flagged_frame_indices.length}</p>
      </article>
    </section>
  );
}
