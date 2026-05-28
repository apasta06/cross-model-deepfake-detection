import { useMemo, useState } from "react";
import { mockAnalysisResult } from "./mocks/analysisResult";
import { AppHeader } from "./components/AppHeader";
import { VerdictHero } from "./components/VerdictHero";
import { ForensicMediaViewer } from "./components/ForensicMediaViewer";
import { EvidencePanel } from "./components/EvidencePanel";
import { FrameThumbnailStrip } from "./components/FrameThumbnailStrip";
import { SelectedFramePanel } from "./components/SelectedFramePanel";
import { FrameEvidenceTable } from "./components/FrameEvidenceTable";
import { FrameRiskTimeline } from "./components/FrameRiskTimeline";

function App() {
  const result = mockAnalysisResult;
  const [selectedFrameIndex, setSelectedFrameIndex] = useState<number>(result.flagged_frame_indices[0] ?? result.frame_results[0]?.frame_index ?? 0);

  const selectedFrame = useMemo(
    () => result.frame_results.find((frame) => frame.frame_index === selectedFrameIndex) ?? result.frame_results[0],
    [result.frame_results, selectedFrameIndex],
  );

  if (!selectedFrame) {
    return null;
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.16),transparent_32rem),linear-gradient(180deg,#0d1117_0%,#111827_45%,#0f172a_100%)] px-3 py-4 text-forensic-text sm:px-4 lg:px-5">
      <div className="mx-auto flex max-w-6xl flex-col gap-4">
        <AppHeader retentionMessage="Uploads are processed locally. Raw media is deleted after analysis. Only audit metadata is retained unless you export a report." />

        <VerdictHero result={result} />

        <ForensicMediaViewer result={result} selectedFrame={selectedFrame} />

        <section className="grid gap-4 lg:grid-cols-2">
          <SelectedFramePanel frame={selectedFrame} flaggedFrameIndices={result.flagged_frame_indices} />
          <EvidencePanel result={result} />
        </section>

        <FrameRiskTimeline
          frames={result.frame_results}
          flaggedFrameIndices={result.flagged_frame_indices}
          selectedFrameIndex={selectedFrameIndex}
          onSelectFrame={setSelectedFrameIndex}
        />

        <FrameThumbnailStrip
          frames={result.frame_results}
          flaggedFrameIndices={result.flagged_frame_indices}
          selectedFrameIndex={selectedFrameIndex}
          onSelectFrame={setSelectedFrameIndex}
        />

        <FrameEvidenceTable
          frames={result.frame_results}
          flaggedFrameIndices={result.flagged_frame_indices}
          selectedFrameIndex={selectedFrameIndex}
          onSelectFrame={setSelectedFrameIndex}
        />
      </div>
    </main>
  );
}

export default App;
