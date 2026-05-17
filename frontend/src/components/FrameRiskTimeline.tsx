import type { FrameResult } from "../types/analysis";
import { formatPercent } from "../lib/format";
import { isFlaggedFrame } from "../lib/risk";

type FrameRiskTimelineProps = {
  frames: FrameResult[];
  flaggedFrameIndices: number[];
  selectedFrameIndex: number;
  onSelectFrame: (frameIndex: number) => void;
};

const WIDTH = 900;
const HEIGHT = 220;
const PADDING = 30;

function pointX(index: number, length: number): number {
  if (length <= 1) {
    return PADDING;
  }
  return PADDING + (index / (length - 1)) * (WIDTH - PADDING * 2);
}

function pointY(probability: number): number {
  return HEIGHT - PADDING - probability * (HEIGHT - PADDING * 2);
}

export function FrameRiskTimeline({ frames, flaggedFrameIndices, selectedFrameIndex, onSelectFrame }: FrameRiskTimelineProps) {
  const polylinePoints = frames.map((frame, index) => `${pointX(index, frames.length)},${pointY(frame.fake_probability)}`).join(" ");

  return (
    <section className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 shadow-forensic backdrop-blur" aria-label="Frame risk timeline">
      <h2 className="text-xl font-semibold text-white">Frame fake-probability timeline</h2>
      <p className="mt-1 text-sm text-forensic-muted">Select any point to inspect that frame in detail.</p>
      <div className="mt-4 overflow-x-auto">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-56 min-w-[700px] w-full" role="img" aria-label="Frame probability timeline chart">
          <rect x={PADDING} y={pointY(1)} width={WIDTH - PADDING * 2} height={pointY(0.74) - pointY(1)} fill="rgba(192,57,43,0.14)" />
          <rect x={PADDING} y={pointY(0.74)} width={WIDTH - PADDING * 2} height={pointY(0.35) - pointY(0.74)} fill="rgba(217,142,4,0.14)" />
          <rect x={PADDING} y={pointY(0.35)} width={WIDTH - PADDING * 2} height={pointY(0) - pointY(0.35)} fill="rgba(46,139,87,0.14)" />

          <line x1={PADDING} x2={WIDTH - PADDING} y1={pointY(0.74)} y2={pointY(0.74)} stroke="rgba(217,142,4,0.7)" strokeDasharray="4 5" />
          <line x1={PADDING} x2={WIDTH - PADDING} y1={pointY(0.35)} y2={pointY(0.35)} stroke="rgba(46,139,87,0.7)" strokeDasharray="4 5" />

          <polyline fill="none" stroke="#38bdf8" strokeWidth="3" points={polylinePoints} />

          {frames.map((frame, index) => {
            const x = pointX(index, frames.length);
            const y = pointY(frame.fake_probability);
            const flagged = isFlaggedFrame(frame.frame_index, flaggedFrameIndices);
            const selected = frame.frame_index === selectedFrameIndex;
            return (
              <g key={frame.frame_index}>
                <circle
                  cx={x}
                  cy={y}
                  r={selected ? 8 : 5}
                  fill={selected ? "#38bdf8" : flagged ? "#C0392B" : "#F3F4F6"}
                  stroke={selected ? "#bae6fd" : "transparent"}
                  strokeWidth={selected ? 2 : 0}
                />
                <foreignObject x={x - 15} y={y - 15} width={30} height={30}>
                  <button
                    type="button"
                    className="h-8 w-8 rounded-full opacity-0"
                    aria-label={`Select frame ${frame.frame_index} at ${frame.timestamp_label} with fake probability ${formatPercent(frame.fake_probability)}`}
                    onClick={() => onSelectFrame(frame.frame_index)}
                  />
                </foreignObject>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}
