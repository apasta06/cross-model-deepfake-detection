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
    <section className="rounded-2xl border border-forensic-border bg-forensic-panel/80 p-4 shadow-forensic backdrop-blur" aria-label="Frame evidence table">
      <h2 className="text-lg font-semibold text-white">Frame evidence table</h2>
      <p className="mt-1 text-sm text-forensic-muted">Each row represents one sampled frame from model scoring.</p>
      <div className="mt-4 hidden md:block">
        <table className="w-full table-fixed border-separate border-spacing-y-1.5 text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-[0.2em] text-forensic-muted">
              <th className="w-[14%] px-3">Frame</th>
              <th className="w-[16%] px-3">Time</th>
              <th className="w-[20%] px-3">Probability</th>
              <th className="w-[18%] px-3">Risk</th>
              <th className="w-[16%] px-3">Flagged</th>
              <th className="w-[16%] px-3">Action</th>
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
                  <td className="rounded-l-xl px-3 py-2 font-mono text-white">{frame.frame_index}</td>
                  <td className="px-3 py-2 font-mono text-forensic-muted">{frame.timestamp_label}</td>
                  <td className="px-3 py-2 font-semibold text-white">{formatPercent(frame.fake_probability)}</td>
                  <td className="px-3 py-2 text-forensic-muted">{frame.risk_label}</td>
                  <td className="px-3 py-2">{flagged ? <span className="text-red-100">Yes</span> : <span className="text-forensic-muted">No</span>}</td>
                  <td className="rounded-r-xl px-3 py-2">
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
      <div className="mt-4 grid gap-2 md:hidden">
        {frames.map((frame) => {
          const selected = frame.frame_index === selectedFrameIndex;
          const flagged = isFlaggedFrame(frame.frame_index, flaggedFrameIndices);
          return (
            <button
              type="button"
              key={frame.frame_index}
              onClick={() => onSelectFrame(frame.frame_index)}
              className={`rounded-2xl border p-3 text-left text-sm ${selected ? "border-forensic-blue bg-forensic-blue/10" : "border-white/10 bg-white/[0.03]"}`}
              aria-label={`Select frame ${frame.frame_index} from evidence cards`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-mono text-white">Frame {frame.frame_index}</span>
                <span className="font-semibold text-white">{formatPercent(frame.fake_probability)}</span>
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-forensic-muted">
                <span>{frame.timestamp_label}</span>
                <span>{frame.risk_label}</span>
                <span>{flagged ? "Flagged" : "Not flagged"}</span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
