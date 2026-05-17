import type { FrameResult } from "../types/analysis";
import { formatPercent } from "../lib/format";
import { isFlaggedFrame } from "../lib/risk";

type FrameEvidenceTableProps = {
  frames: FrameResult[];
  flaggedFrameIndices: number[];
  selectedFrameIndex: number;
  onSelectFrame: (frameIndex: number) => void;
};

export function FrameEvidenceTable({ frames, flaggedFrameIndices, selectedFrameIndex, onSelectFrame }: FrameEvidenceTableProps) {
  return (
    <section className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 shadow-forensic backdrop-blur" aria-label="Frame evidence table">
      <h2 className="text-xl font-semibold text-white">Frame evidence table</h2>
      <p className="mt-1 text-sm text-forensic-muted">Each row represents one sampled frame from model scoring.</p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-y-2 text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-[0.2em] text-forensic-muted">
              <th className="px-3">Frame</th>
              <th className="px-3">Timestamp</th>
              <th className="px-3">Probability</th>
              <th className="px-3">Risk</th>
              <th className="px-3">Flagged</th>
              <th className="px-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {frames.map((frame) => {
              const selected = frame.frame_index === selectedFrameIndex;
              const flagged = isFlaggedFrame(frame.frame_index, flaggedFrameIndices);
              return (
                <tr
                  key={frame.frame_index}
                  className={`cursor-pointer rounded-xl border ${selected ? "border-forensic-blue bg-forensic-blue/10" : "border-white/10 bg-white/[0.02] hover:bg-white/[0.05]"}`}
                  onClick={() => onSelectFrame(frame.frame_index)}
                  data-testid={`frame-row-${frame.frame_index}`}
                  aria-label={`Frame row ${frame.frame_index}`}
                >
                  <td className="rounded-l-xl px-3 py-3 font-mono text-white">{frame.frame_index}</td>
                  <td className="px-3 py-3 font-mono text-forensic-muted">{frame.timestamp_label}</td>
                  <td className="px-3 py-3 font-semibold text-white">{formatPercent(frame.fake_probability)}</td>
                  <td className="px-3 py-3 text-forensic-muted">{frame.risk_label}</td>
                  <td className="px-3 py-3">{flagged ? <span className="text-red-100">Yes</span> : <span className="text-forensic-muted">No</span>}</td>
                  <td className="rounded-r-xl px-3 py-3">
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onSelectFrame(frame.frame_index);
                      }}
                      className="rounded-lg border border-forensic-blue/40 bg-forensic-blue/10 px-2 py-1 text-xs text-sky-100 hover:border-forensic-blue"
                      aria-label={`Select frame ${frame.frame_index} from evidence table`}
                    >
                      Select
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
