import type { AnalysisResult, FrameResult } from "../types/analysis";
import { formatPercent } from "../lib/format";

type ForensicMediaViewerProps = {
  result: AnalysisResult;
  selectedFrame: FrameResult;
};

export function ForensicMediaViewer({ result, selectedFrame }: ForensicMediaViewerProps) {
  return (
    <article className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 shadow-forensic backdrop-blur">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Forensic viewer</h2>
          <p className="text-sm text-forensic-muted">
            {result.filename} - {result.model_used} - {result.media_metadata.width}x{result.media_metadata.height}
          </p>
        </div>
        <span className="rounded-full border border-forensic-fake/40 bg-forensic-fake/15 px-3 py-1 text-sm font-medium text-red-100">Mock analysis fixture</span>
      </div>
      <div className="mt-5 grid min-h-72 place-items-center rounded-2xl border border-dashed border-white/15 bg-black/30 p-8 text-center">
        <div>
          <p className="text-lg font-semibold text-white">Video preview placeholder</p>
          <p className="mt-2 max-w-xl text-sm text-forensic-muted">Step 2 keeps placeholder media while frame evidence interactions are wired.</p>
          <p className="mt-4 text-sm text-sky-200">
            Selected frame {selectedFrame.frame_index} at {selectedFrame.timestamp_label} - fake probability {formatPercent(selectedFrame.fake_probability)}
          </p>
        </div>
      </div>
    </article>
  );
}
