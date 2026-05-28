import type { AnalysisResult, FrameResult } from "../types/analysis";
import { formatPercent } from "../lib/format";

type ForensicMediaViewerProps = {
  result: AnalysisResult;
  selectedFrame: FrameResult;
  mediaPreviewUrl?: string | null;
};

export function ForensicMediaViewer({ result, selectedFrame, mediaPreviewUrl }: ForensicMediaViewerProps) {
  const durationSeconds = result.media_metadata.duration_seconds ?? 0;
  const progressPercent = durationSeconds > 0 ? Math.min(100, Math.round((selectedFrame.timestamp_seconds / durationSeconds) * 100)) : 0;
  const dimensions = result.media_metadata.width && result.media_metadata.height ? `${result.media_metadata.width}x${result.media_metadata.height}` : "Dimensions unavailable";

  return (
    <article className="rounded-2xl border border-forensic-border bg-forensic-panel/80 p-4 shadow-forensic backdrop-blur">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Forensic viewer</h2>
          <p className="text-sm text-forensic-muted">
            {result.filename} - {result.model_used} - {dimensions}
          </p>
        </div>
        <span className="rounded-full border border-forensic-real/40 bg-forensic-real/15 px-3 py-1 text-sm font-medium text-emerald-100">Analysis complete</span>
      </div>
      <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-black shadow-2xl">
        <div className="relative aspect-[16/8.2] max-h-[420px] bg-[radial-gradient(circle_at_25%_20%,rgba(56,189,248,0.2),transparent_24rem),linear-gradient(135deg,#111827,#020617_55%,#1e1b4b)]">
          {mediaPreviewUrl && result.input_type === "video" ? (
            <video src={mediaPreviewUrl} controls className="h-full w-full object-contain" aria-label={`Uploaded video ${result.filename}`} />
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
    </article>
  );
}
