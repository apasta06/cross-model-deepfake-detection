import type { FrameResult } from "../types/analysis";
import { formatPercent } from "../lib/format";
import { isFlaggedFrame, riskChipByKey } from "../lib/risk";

type SelectedFramePanelProps = {
  frame: FrameResult;
  flaggedFrameIndices: number[];
};

export function SelectedFramePanel({ frame, flaggedFrameIndices }: SelectedFramePanelProps) {
  const flagged = isFlaggedFrame(frame.frame_index, flaggedFrameIndices);
  return (
    <aside className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 shadow-forensic backdrop-blur" aria-label="Selected frame panel">
      <h2 className="text-xl font-semibold text-white">Selected frame details</h2>
      <img src={frame.thumbnail_url} alt={`Selected frame ${frame.frame_index}`} className="mt-4 aspect-video w-full rounded-2xl border border-white/10 object-cover" />
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <dt className="text-forensic-muted">Frame index</dt>
          <dd className="mt-1 font-mono text-white">{frame.frame_index}</dd>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <dt className="text-forensic-muted">Timestamp</dt>
          <dd className="mt-1 font-mono text-white">{frame.timestamp_label}</dd>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <dt className="text-forensic-muted">Fake probability</dt>
          <dd className="mt-1 font-semibold text-white">{formatPercent(frame.fake_probability)}</dd>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <dt className="text-forensic-muted">Flag status</dt>
          <dd className="mt-1 text-white">{flagged ? "Flagged" : "Not flagged"}</dd>
        </div>
      </dl>
      <div className="mt-4 flex gap-2">
        <span className={`rounded-full border px-2 py-0.5 text-xs ${riskChipByKey[frame.risk_key]}`}>{frame.risk_label}</span>
        {flagged ? <span className="rounded-full border border-forensic-fake/30 bg-forensic-fake/10 px-2 py-0.5 text-xs text-red-100">Needs review</span> : null}
      </div>
    </aside>
  );
}
