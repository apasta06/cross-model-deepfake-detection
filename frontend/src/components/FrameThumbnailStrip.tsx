import type { FrameResult } from "../types/analysis";
import { formatPercent } from "../lib/format";
import { isFlaggedFrame, riskChipByKey } from "../lib/risk";

type FrameThumbnailStripProps = {
  frames: FrameResult[];
  flaggedFrameIndices: number[];
  selectedFrameIndex: number;
  onSelectFrame: (frameIndex: number) => void;
};

export function FrameThumbnailStrip({ frames, flaggedFrameIndices, selectedFrameIndex, onSelectFrame }: FrameThumbnailStripProps) {
  return (
    <section className="rounded-2xl border border-forensic-border bg-forensic-panel/80 p-4 shadow-forensic backdrop-blur" aria-label="Frame thumbnail strip">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Sampled frame evidence</h2>
          <p className="text-sm text-forensic-muted">Click any frame to inspect timestamp and fake probability details.</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
        {frames.map((frame) => {
          const selected = frame.frame_index === selectedFrameIndex;
          const flagged = isFlaggedFrame(frame.frame_index, flaggedFrameIndices);
          return (
            <button
              type="button"
              key={frame.frame_index}
              aria-pressed={selected}
              aria-label={`Select frame ${frame.frame_index} at ${frame.timestamp_label} with fake probability ${formatPercent(frame.fake_probability)}`}
              onClick={() => onSelectFrame(frame.frame_index)}
              className={`w-full overflow-hidden rounded-2xl border bg-black/30 text-left transition ${
                selected ? "border-forensic-blue ring-2 ring-forensic-blue/50" : "border-white/10 hover:border-forensic-blue/40"
              }`}
            >
              {frame.thumbnail_url ? (
                <img src={frame.thumbnail_url} alt={`Frame ${frame.frame_index} at ${frame.timestamp_label}`} className="aspect-video w-full object-cover" />
              ) : (
                <div className="flex aspect-video w-full items-center justify-center bg-slate-950/80 p-3 text-center">
                  <div>
                    <p className="font-mono text-sm text-white">Frame {frame.frame_index}</p>
                    <p className="mt-1 text-xs text-forensic-muted">{frame.timestamp_label}</p>
                  </div>
                </div>
              )}
              <div className="space-y-2 p-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-forensic-muted">{frame.timestamp_label}</span>
                  <span className="font-semibold text-white">{formatPercent(frame.fake_probability)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full border px-2 py-0.5 text-xs ${riskChipByKey[frame.risk_key]}`}>{frame.risk_label}</span>
                  {flagged ? <span className="rounded-full border border-forensic-fake/30 bg-forensic-fake/10 px-2 py-0.5 text-xs text-red-100">Flagged</span> : null}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
