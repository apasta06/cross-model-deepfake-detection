import { useCallback, useEffect, useRef, useState } from "react";
import type { AnalysisResult, FrameResult } from "../types/analysis";
import { formatPercent } from "../lib/format";

type ForensicMediaViewerProps = {
  result: AnalysisResult;
  selectedFrame: FrameResult;
  mediaPreviewUrl?: string | null;
  showHeatmap: boolean;
  onToggleHeatmap: (value: boolean) => void;
};

// Tolerance (seconds) between video.currentTime and the selected frame's
// timestamp within which the heatmap overlay is considered aligned.
const ALIGN_TOLERANCE_SECONDS = 0.4;

type OverlayRect = { left: number; top: number; width: number; height: number };

// Map a face box (in original-frame px) into rendered-element px, accounting
// for object-contain letterboxing. Returns null if geometry isn't ready.
function computeOverlayRect(
  faceBox: [number, number, number, number],
  frameWidth: number,
  frameHeight: number,
  videoEl: HTMLVideoElement,
): OverlayRect | null {
  const intrinsicW = videoEl.videoWidth || frameWidth;
  const intrinsicH = videoEl.videoHeight || frameHeight;
  const elW = videoEl.clientWidth;
  const elH = videoEl.clientHeight;
  if (!intrinsicW || !intrinsicH || !elW || !elH) {
    return null;
  }

  // object-contain: the content is scaled by the smaller ratio and centered,
  // producing letterbox bars on the axis with extra room.
  const scale = Math.min(elW / intrinsicW, elH / intrinsicH);
  const displayedW = intrinsicW * scale;
  const displayedH = intrinsicH * scale;
  const offsetX = (elW - displayedW) / 2;
  const offsetY = (elH - displayedH) / 2;

  // The box was recorded in the original-frame space (frameWidth/Height),
  // which may differ from the element's intrinsic size if they ever diverge;
  // normalize through the frame space first, then into displayed px.
  const normX = intrinsicW / frameWidth;
  const normY = intrinsicH / frameHeight;
  const [x1, y1, x2, y2] = faceBox;

  const left = offsetX + x1 * normX * scale;
  const top = offsetY + y1 * normY * scale;
  const width = (x2 - x1) * normX * scale;
  const height = (y2 - y1) * normY * scale;
  return { left, top, width, height };
}

// Grad-CAM colors show WHERE the model looked, not WHETHER a frame is fake -
// every overlay is red-where-it-looked regardless of verdict. To make a real
// frame and a fake frame distinguishable at a glance, we drive the overlay's
// border, opacity, and a verdict chip from the frame's fake_probability vs the
// model threshold. The heatmap pixels themselves are unchanged (that would be
// a backend colormap change); only the framing communicates the verdict.
type VerdictStyle = {
  tier: "real" | "uncertain" | "fake";
  label: string;
  ringClass: string;
  chipClass: string;
  opacity: number;
};

function verdictStyleFor(probability: number, threshold: number): VerdictStyle {
  const pct = Math.round(probability * 100);
  // "Uncertain" band sits just below the fake threshold; tune the 0.1 margin
  // here if you want a wider/narrower grey zone.
  const uncertainFloor = Math.max(0, threshold - 0.1);
  if (probability >= threshold) {
    return {
      tier: "fake",
      label: `LIKELY FAKE - ${pct}%`,
      ringClass: "ring-2 ring-red-400/80",
      chipClass: "border-red-300/50 bg-red-950/85 text-red-100",
      opacity: 0.85,
    };
  }
  if (probability >= uncertainFloor) {
    return {
      tier: "uncertain",
      label: `UNCERTAIN - ${pct}%`,
      ringClass: "ring-2 ring-amber-300/70",
      chipClass: "border-amber-300/50 bg-amber-950/80 text-amber-100",
      opacity: 0.6,
    };
  }
  return {
    tier: "real",
    label: `LIKELY REAL - ${pct}%`,
    ringClass: "ring-2 ring-emerald-300/70",
    chipClass: "border-emerald-300/50 bg-emerald-950/80 text-emerald-100",
    opacity: 0.4,
  };
}

export function ForensicMediaViewer({ result, selectedFrame, mediaPreviewUrl, showHeatmap, onToggleHeatmap }: ForensicMediaViewerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isPaused, setIsPaused] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [overlayRect, setOverlayRect] = useState<OverlayRect | null>(null);

  const durationSeconds = result.media_metadata.duration_seconds ?? 0;
  const progressPercent = durationSeconds > 0 ? Math.min(100, Math.round((selectedFrame.timestamp_seconds / durationSeconds) * 100)) : 0;
  const dimensions = result.media_metadata.width && result.media_metadata.height ? `${result.media_metadata.width}x${result.media_metadata.height}` : "Dimensions unavailable";

  // Does this result carry any heatmap data at all? Controls toggle enablement.
  const hasAnyHeatmap = result.frame_results.some((frame) => Boolean(frame.heatmap_url));
  const isVideo = Boolean(mediaPreviewUrl) && result.input_type === "video";

  const recomputeOverlay = useCallback(() => {
    const videoEl = videoRef.current;
    if (!videoEl || !selectedFrame.face_box || !selectedFrame.frame_width || !selectedFrame.frame_height) {
      setOverlayRect(null);
      return;
    }
    setOverlayRect(
      computeOverlayRect(selectedFrame.face_box, selectedFrame.frame_width, selectedFrame.frame_height, videoEl),
    );
  }, [selectedFrame]);

  // Seek to the selected frame's timestamp and pause, so selecting a frame
  // brings the correctly-aligned overlay into view (hide-on-play behavior).
  useEffect(() => {
    const videoEl = videoRef.current;
    if (!videoEl || !isVideo) {
      return;
    }
    if (Number.isFinite(selectedFrame.timestamp_seconds)) {
      try {
        videoEl.pause();
        videoEl.currentTime = selectedFrame.timestamp_seconds;
      } catch {
        // Seeking before metadata is ready can throw; ignored, retried on load.
      }
    }
  }, [selectedFrame, isVideo]);

  // Recompute overlay geometry on resize of the video element.
  useEffect(() => {
    const videoEl = videoRef.current;
    if (!videoEl) {
      return;
    }
    const observer = new ResizeObserver(() => recomputeOverlay());
    observer.observe(videoEl);
    return () => observer.disconnect();
  }, [recomputeOverlay]);

  const isAligned = Math.abs(currentTime - selectedFrame.timestamp_seconds) < ALIGN_TOLERANCE_SECONDS;
  const overlayVisible = showHeatmap && isPaused && isAligned && Boolean(selectedFrame.heatmap_url) && Boolean(overlayRect);
  const heatmapUnavailableForFrame = showHeatmap && !selectedFrame.heatmap_url;

  // Verdict styling for the overlay: probability vs the model's video
  // threshold (falls back to 0.6 if the payload doesn't carry one).
  const videoThreshold = result.report_payload?.video_threshold ?? 0.6;
  const verdictStyle = verdictStyleFor(selectedFrame.fake_probability, videoThreshold);

  return (
    <article className="rounded-2xl border border-forensic-border bg-forensic-panel/80 p-4 shadow-forensic backdrop-blur">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Forensic viewer</h2>
          <p className="text-sm text-forensic-muted">
            {result.filename} - {result.model_used} - {dimensions}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className={`flex items-center gap-2 text-xs font-medium ${hasAnyHeatmap ? "text-sky-100" : "text-forensic-muted"}`}>
            <input
              type="checkbox"
              checked={showHeatmap}
              disabled={!hasAnyHeatmap}
              onChange={(event) => onToggleHeatmap(event.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-slate-900 accent-forensic-blue disabled:cursor-not-allowed"
              aria-label="Show heatmap overlay"
            />
            Show heatmap
          </label>
          <span className="rounded-full border border-forensic-real/40 bg-forensic-real/15 px-3 py-1 text-sm font-medium text-emerald-100">Analysis complete</span>
        </div>
      </div>
      <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-black shadow-2xl">
        <div className="relative aspect-[16/8.2] max-h-[420px] bg-[radial-gradient(circle_at_25%_20%,rgba(56,189,248,0.2),transparent_24rem),linear-gradient(135deg,#111827,#020617_55%,#1e1b4b)]">
          {isVideo ? (
            <video
              ref={videoRef}
              src={mediaPreviewUrl ?? undefined}
              controls
              className="h-full w-full object-contain"
              aria-label={`Uploaded video ${result.filename}`}
              onLoadedMetadata={recomputeOverlay}
              onPlay={() => setIsPaused(false)}
              onPause={() => setIsPaused(true)}
              onSeeked={recomputeOverlay}
              onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
            />
          ) : null}
          {mediaPreviewUrl && result.input_type === "image" ? <img src={mediaPreviewUrl} alt={`Uploaded media ${result.filename}`} className="h-full w-full object-contain" /> : null}
          {!mediaPreviewUrl ? (
            <div className="flex h-full w-full items-center justify-center p-6 text-center">
              <div>
                <p className="text-lg font-semibold text-white">Media preview unavailable</p>
                <p className="mt-2 text-sm text-forensic-muted">The analysis data is available, but the local upload preview is not attached to this result.</p>
              </div>
            </div>
          ) : null}
          {overlayVisible && overlayRect ? (
            <>
              <img
                src={selectedFrame.heatmap_url ?? undefined}
                alt={`Heatmap overlay for frame ${selectedFrame.frame_index}`}
                className={`pointer-events-none absolute rounded-md ${verdictStyle.ringClass}`}
                style={{
                  left: overlayRect.left,
                  top: overlayRect.top,
                  width: overlayRect.width,
                  height: overlayRect.height,
                  opacity: verdictStyle.opacity,
                }}
              />
              <span
                className={`pointer-events-none absolute rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide ${verdictStyle.chipClass}`}
                style={{
                  left: overlayRect.left,
                  top: Math.max(0, overlayRect.top - 22),
                }}
              >
                {verdictStyle.label}
              </span>
            </>
          ) : null}
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black via-transparent to-black/30" />
          <div className="absolute left-4 top-4 flex flex-wrap gap-2 text-xs font-medium">
            <span className="rounded-full border border-sky-300/40 bg-sky-950/70 px-3 py-1 text-sky-100">Uploaded {result.input_type} loaded</span>
            <span className="rounded-full border border-red-300/40 bg-red-950/60 px-3 py-1 text-red-100">Selected frame {selectedFrame.frame_index}</span>
          </div>
          <div className="absolute bottom-3 left-3 right-3 rounded-2xl border border-white/10 bg-slate-950/75 p-3 backdrop-blur">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-forensic-muted">Selected timestamp</p>
                <p className="mt-1 text-xl font-semibold text-white">{selectedFrame.timestamp_label}</p>
              </div>
              <div className="text-left sm:text-right">
                <p className="text-xs uppercase tracking-[0.22em] text-forensic-muted">Fake probability</p>
                <p className="mt-1 text-xl font-semibold text-red-100">{formatPercent(selectedFrame.fake_probability)}</p>
              </div>
            </div>
            <div className="mt-3 h-2 rounded-full bg-white/10">
              <div className="h-2 rounded-full bg-gradient-to-r from-sky-400 via-amber-300 to-red-400" style={{ width: `${progressPercent}%` }} />
            </div>
            <div className="mt-2 flex justify-between text-xs text-forensic-muted">
              <span>00:00</span>
              <span>{durationSeconds > 0 ? `${durationSeconds.toFixed(1)}s total` : "Unknown duration"}</span>
            </div>
          </div>
        </div>
        <div className="grid gap-2 border-t border-white/10 bg-slate-950/80 p-3 text-xs sm:grid-cols-4">
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5">
            <p className="text-forensic-muted">Upload status</p>
            <p className="mt-1 font-semibold text-white">Complete</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5">
            <p className="text-forensic-muted">Frames sampled</p>
            <p className="mt-1 font-semibold text-white">{result.frame_stats.sampled_frames}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5">
            <p className="text-forensic-muted">Flagged frames</p>
            <p className="mt-1 font-semibold text-white">{result.flagged_frame_indices.length}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5">
            <p className="text-forensic-muted">Report</p>
            <p className="mt-1 font-semibold text-white">Ready</p>
          </div>
        </div>
      </div>
      {showHeatmap ? (
        <p className="mt-3 text-xs text-forensic-muted">
          {heatmapUnavailableForFrame
            ? "Heatmap unavailable for this frame (no reliable face box was detected). Select another frame to view its overlay."
            : "Heatmap aligns to the selected frame and is shown while paused. Press play to hide it; the overlay would drift as the face moves."}
        </p>
      ) : null}
    </article>
  );
}
