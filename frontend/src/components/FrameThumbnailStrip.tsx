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
    <section className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 shadow-forensic backdrop-blur" aria-label="Frame thumbnail strip">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Sampled frame evidence</h2>
          <p className="text-sm text-forensic-muted">Click any frame to inspect timestamp and fake probability details.</p>
        </div>
      </div>
      <div className="mt-5 flex gap-4 overflow-x-auto pb-2">
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
              className={`w-56 shrink-0 overflow-hidden rounded-2xl border bg-black/30 text-left transition ${
                selected ? "border-forensic-blue ring-2 ring-forensic-blue/50" : "border-white/10 hover:border-forensic-blue/40"
              }`}
            >
              <img src={frame.thumbnail_url} alt={`Frame ${frame.frame_index} at ${frame.timestamp_label}`} className="aspect-video w-full object-cover" />
              <div className="space-y-2 p-3 text-sm">
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
