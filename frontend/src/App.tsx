import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "./components/AppHeader";
import { AnalysisControls } from "./components/AnalysisControls";
import { VerdictHero } from "./components/VerdictHero";
import { ForensicMediaViewer } from "./components/ForensicMediaViewer";
import { EvidencePanel } from "./components/EvidencePanel";
import { FrameThumbnailStrip } from "./components/FrameThumbnailStrip";
import { SelectedFramePanel } from "./components/SelectedFramePanel";
import { FrameEvidenceTable } from "./components/FrameEvidenceTable";
import { FrameRiskTimeline } from "./components/FrameRiskTimeline";
import { analyzeMedia, getModels } from "./lib/api";
import type { AnalysisResult, ModelInfo, ModelKey } from "./types/analysis";

const DEFAULT_SAMPLE_FRAMES = 12;
const DEFAULT_MODEL: ModelKey = "EFFICIENTB0";

function clampSampleFrames(value: number): number {
  if (!Number.isFinite(value)) {
    return 1;
  }
  return Math.min(120, Math.max(1, Math.round(value)));
}

function App() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelKey | "">("");
  const [sampleFrames, setSampleFrames] = useState(DEFAULT_SAMPLE_FRAMES);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [mediaPreviewUrl, setMediaPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [selectedFrameIndex, setSelectedFrameIndex] = useState<number | null>(null);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoadingModels(true);
    getModels()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setModels(payload.models);
        setSelectedModel((current) => current || payload.models.find((model) => model.key === DEFAULT_MODEL)?.key || payload.models[0]?.key || "");
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) {
          return;
        }
        setError(err instanceof Error ? err.message : "Unable to load backend models.");
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingModels(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedFile) {
      setMediaPreviewUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(selectedFile);
    setMediaPreviewUrl(objectUrl);
    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [selectedFile]);

  const selectedFrame = useMemo(
    () => result?.frame_results.find((frame) => frame.frame_index === selectedFrameIndex) ?? result?.frame_results[0] ?? null,
    [result, selectedFrameIndex],
  );

  async function handleAnalyze() {
    if (!selectedFile || !selectedModel) {
      setError("Choose a media file and model before running analysis.");
      return;
    }
    setIsAnalyzing(true);
    setError(null);
    try {
      const nextResult = await analyzeMedia(selectedFile, selectedModel, sampleFrames);
      setResult(nextResult);
      setSelectedFrameIndex(nextResult.flagged_frame_indices[0] ?? nextResult.frame_results[0]?.frame_index ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed unexpectedly.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.16),transparent_32rem),linear-gradient(180deg,#0d1117_0%,#111827_45%,#0f172a_100%)] px-3 py-4 text-forensic-text sm:px-4 lg:px-5">
      <div className="mx-auto flex max-w-6xl flex-col gap-4">
        <AppHeader retentionMessage="Uploads are processed locally. Raw media is deleted after analysis. Only audit metadata is retained unless you export a report." />

        <AnalysisControls
          models={models}
          selectedModel={selectedModel}
          sampleFrames={sampleFrames}
          selectedFile={selectedFile}
          isLoadingModels={isLoadingModels}
          isAnalyzing={isAnalyzing}
          error={error}
          onModelChange={setSelectedModel}
          onSampleFramesChange={(value) => setSampleFrames(clampSampleFrames(value))}
          onFileChange={(file) => {
            setSelectedFile(file);
            setError(null);
          }}
          onAnalyze={handleAnalyze}
        />

        {result && selectedFrame ? (
          <>
            <VerdictHero result={result} />

            <ForensicMediaViewer result={result} selectedFrame={selectedFrame} mediaPreviewUrl={mediaPreviewUrl} />

            <section className="grid gap-4 lg:grid-cols-2">
              <SelectedFramePanel frame={selectedFrame} flaggedFrameIndices={result.flagged_frame_indices} />
              <EvidencePanel result={result} />
            </section>

            <FrameRiskTimeline
              frames={result.frame_results}
              flaggedFrameIndices={result.flagged_frame_indices}
              selectedFrameIndex={selectedFrame.frame_index}
              onSelectFrame={setSelectedFrameIndex}
            />

            <FrameThumbnailStrip
              frames={result.frame_results}
              flaggedFrameIndices={result.flagged_frame_indices}
              selectedFrameIndex={selectedFrame.frame_index}
              onSelectFrame={setSelectedFrameIndex}
            />

            <FrameEvidenceTable
              frames={result.frame_results}
              flaggedFrameIndices={result.flagged_frame_indices}
              selectedFrameIndex={selectedFrame.frame_index}
              onSelectFrame={setSelectedFrameIndex}
            />
          </>
        ) : (
          <section className="rounded-2xl border border-dashed border-forensic-border bg-forensic-panel/40 p-6 text-center shadow-forensic backdrop-blur" aria-label="Empty analysis state">
            <h2 className="text-lg font-semibold text-white">No analysis loaded yet</h2>
            <p className="mt-2 text-sm text-forensic-muted">Upload media and run analysis to populate the forensic viewer, frame timeline, and evidence table.</p>
          </section>
        )}
      </div>
    </main>
  );
}

export default App;
