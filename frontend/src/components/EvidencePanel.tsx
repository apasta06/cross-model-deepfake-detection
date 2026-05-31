import type { AnalysisResult } from "../types/analysis";
import { reportUrl } from "../lib/api";

type EvidencePanelProps = {
  result: AnalysisResult;
};

export function EvidencePanel({ result }: EvidencePanelProps) {
  return (
    <aside className="rounded-2xl border border-forensic-border bg-forensic-panel/80 p-4 shadow-forensic backdrop-blur">
      <h2 className="text-lg font-semibold text-white">Evidence summary</h2>
      <p className="mt-2 text-sm leading-5 text-forensic-muted">{result.summary_text}</p>
      {result.warnings.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-forensic-uncertain/35 bg-forensic-uncertain/10 p-3 text-sm text-amber-100">
          {result.warnings.join(" ")}
        </div>
      ) : null}
      <div className="mt-4 space-y-2">
        {result.evidence_paths.map((asset) => (
          <div key={asset.label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
            <p className="font-semibold text-white">{asset.label}</p>
            <p className="mt-1 text-sm text-forensic-muted">{asset.description}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-2xl border border-forensic-blue/25 bg-forensic-blue/10 p-3">
          <p className="text-forensic-muted">Case ID</p>
          <p className="mt-1 font-mono text-white">{result.analysis_id}</p>
        </div>
        <div className="rounded-2xl border border-forensic-real/25 bg-forensic-real/10 p-3">
          <p className="text-forensic-muted">Export status</p>
          <p className="mt-1 font-semibold text-white">Ready</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <a
          href={reportUrl(result.analysis_id, "html")}
          className="rounded-xl border border-forensic-blue/40 bg-forensic-blue/10 px-3 py-2 text-sm font-semibold text-sky-100 hover:border-forensic-blue"
        >
          Download HTML report
        </a>
        <a
          href={reportUrl(result.analysis_id, "json")}
          className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm font-semibold text-white hover:border-forensic-blue/50"
        >
          Download JSON report
        </a>
      </div>
    </aside>
  );
}
