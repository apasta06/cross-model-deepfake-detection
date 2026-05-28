import type { ModelInfo, ModelKey } from "../types/analysis";

const ACCEPTED_MEDIA = ".jpg,.jpeg,.png,.bmp,.mp4,.avi,.mov,.mkv,.mts,.webm";

type AnalysisControlsProps = {
  models: ModelInfo[];
  selectedModel: ModelKey | "";
  sampleFrames: number;
  selectedFile: File | null;
  isLoadingModels: boolean;
  isAnalyzing: boolean;
  error: string | null;
  onModelChange: (model: ModelKey) => void;
  onSampleFramesChange: (sampleFrames: number) => void;
  onFileChange: (file: File | null) => void;
  onAnalyze: () => void;
};

export function AnalysisControls({
  models,
  selectedModel,
  sampleFrames,
  selectedFile,
  isLoadingModels,
  isAnalyzing,
  error,
  onModelChange,
  onSampleFramesChange,
  onFileChange,
  onAnalyze,
}: AnalysisControlsProps) {
  const canAnalyze = Boolean(selectedFile && selectedModel && !isAnalyzing && !isLoadingModels);

  return (
    <section className="rounded-2xl border border-forensic-border bg-forensic-panel/80 p-4 shadow-forensic backdrop-blur" aria-label="Upload analysis controls">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Upload media for analysis</h2>
          <p className="mt-1 text-sm text-forensic-muted">Choose an image or video, select a model, then run backend inference.</p>
        </div>
        <span className="rounded-full border border-forensic-blue/40 bg-forensic-blue/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-sky-100">
          {isLoadingModels ? "Loading models" : "API ready"}
        </span>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[1.4fr_1fr_0.7fr_auto] lg:items-end">
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-forensic-muted">Media file</span>
          <input
            type="file"
            accept={ACCEPTED_MEDIA}
            onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
            className="mt-2 block w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-2 text-sm text-forensic-muted file:mr-3 file:rounded-lg file:border-0 file:bg-forensic-blue/20 file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-sky-100 hover:border-forensic-blue/50"
            aria-label="Select media file"
          />
        </label>

        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-forensic-muted">Model</span>
          <select
            value={selectedModel}
            onChange={(event) => onModelChange(event.target.value as ModelKey)}
            disabled={isLoadingModels || models.length === 0}
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-2 text-sm text-white disabled:cursor-not-allowed disabled:text-forensic-muted"
            aria-label="Select analysis model"
          >
            <option value="" disabled>
              {isLoadingModels ? "Loading models..." : "Select a model"}
            </option>
            {models.map((model) => (
              <option key={model.key} value={model.key}>
                {model.key}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-forensic-muted">Sample frames</span>
          <input
            type="number"
            min={1}
            max={120}
            value={sampleFrames}
            onChange={(event) => onSampleFramesChange(Number(event.target.value))}
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-2 text-sm text-white"
            aria-label="Sample frames"
          />
        </label>

        <button
          type="button"
          onClick={onAnalyze}
          disabled={!canAnalyze}
          className="rounded-xl border border-forensic-blue/50 bg-forensic-blue/20 px-4 py-2 text-sm font-semibold text-sky-100 transition hover:border-forensic-blue disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/[0.03] disabled:text-forensic-muted"
        >
          {isAnalyzing ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {selectedFile ? <p className="mt-3 text-xs text-forensic-muted">Selected: {selectedFile.name}</p> : null}
      {error ? <div className="mt-3 rounded-xl border border-forensic-fake/40 bg-forensic-fake/10 p-3 text-sm text-red-100">{error}</div> : null}
    </section>
  );
}
