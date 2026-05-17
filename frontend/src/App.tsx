import { mockAnalysisResult } from "./mocks/analysisResult";

const riskTone = {
  likely_real: "border-forensic-real/40 text-forensic-real",
  uncertain: "border-forensic-uncertain/40 text-forensic-uncertain",
  likely_fake: "border-forensic-fake/50 text-forensic-fake",
} as const;

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function App() {
  const result = mockAnalysisResult;
  const suspiciousFrames = [...result.frame_results].sort((left, right) => right.fake_probability - left.fake_probability).slice(0, 4);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.16),transparent_32rem),linear-gradient(180deg,#0d1117_0%,#111827_45%,#0f172a_100%)] px-4 py-6 text-forensic-text sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="flex flex-col gap-4 rounded-3xl border border-forensic-border bg-forensic-panel/70 p-5 shadow-forensic backdrop-blur md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.28em] text-forensic-blue">Deepfake Forensics</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white md:text-5xl">ML evidence review workstation</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-forensic-muted md:text-base">
              Upload media, inspect frame-level fake probabilities, identify suspicious frames, and prepare audit-ready reports.
            </p>
          </div>
          <div className="rounded-2xl border border-forensic-blue/35 bg-forensic-blue/10 p-4 text-sm text-sky-100 md:max-w-sm">
            Uploads are processed locally. Raw media is deleted after analysis. Only audit metadata is retained unless you export a report.
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3" aria-label="Analysis summary">
          <article className={`rounded-3xl border bg-forensic-panel/80 p-5 backdrop-blur ${riskTone[result.risk_level]}`}>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Final verdict</p>
            <p className="mt-4 text-3xl font-bold">{result.verdict}</p>
          </article>
          <article className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Confidence</p>
            <p className="mt-4 text-3xl font-bold text-white">{formatPercent(result.confidence_score)}</p>
          </article>
          <article className={`rounded-3xl border bg-forensic-panel/80 p-5 backdrop-blur ${riskTone[result.risk_level]}`}>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Flagged frames</p>
            <p className="mt-4 text-3xl font-bold">{result.flagged_frame_indices.length}</p>
          </article>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <article className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 shadow-forensic backdrop-blur">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">Forensic viewer</h2>
                <p className="text-sm text-forensic-muted">{result.filename} · {result.model_used} · {result.media_metadata.width}x{result.media_metadata.height}</p>
              </div>
              <span className="rounded-full border border-forensic-fake/40 bg-forensic-fake/15 px-3 py-1 text-sm font-medium text-red-100">
                Mock analysis fixture
              </span>
            </div>
            <div className="mt-5 grid min-h-72 place-items-center rounded-2xl border border-dashed border-white/15 bg-black/30 p-8 text-center">
              <div>
                <p className="text-lg font-semibold text-white">Video preview placeholder</p>
                <p className="mt-2 max-w-xl text-sm text-forensic-muted">
                  Step 2 will replace this shell with synchronized media, timeline, thumbnail, and frame detail interactions.
                </p>
              </div>
            </div>
          </article>

          <aside className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 shadow-forensic backdrop-blur">
            <h2 className="text-xl font-semibold text-white">Evidence summary</h2>
            <p className="mt-3 text-sm leading-6 text-forensic-muted">{result.summary_text}</p>
            <div className="mt-5 space-y-3">
              {result.evidence_paths.map((asset) => (
                <div key={asset.label} className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="font-semibold text-white">{asset.label}</p>
                  <p className="mt-1 text-sm text-forensic-muted">{asset.description}</p>
                </div>
              ))}
            </div>
          </aside>
        </section>

        <section className="rounded-3xl border border-forensic-border bg-forensic-panel/80 p-5 shadow-forensic backdrop-blur" aria-label="Suspicious frame placeholders">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">Most suspicious sampled frames</h2>
              <p className="text-sm text-forensic-muted">Placeholder thumbnails prove the data contract before real extraction is wired.</p>
            </div>
            <p className="font-mono text-sm text-forensic-muted">{result.frame_stats.sampled_frames} sampled frames</p>
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {suspiciousFrames.map((frame) => (
              <figure key={frame.frame_index} className="overflow-hidden rounded-2xl border border-forensic-fake/35 bg-black/30">
                <img src={frame.thumbnail_url} alt={`Frame ${frame.frame_index} at ${frame.timestamp_label}`} className="aspect-video w-full object-cover" />
                <figcaption className="flex items-center justify-between p-3 text-sm">
                  <span className="font-mono text-forensic-muted">{frame.timestamp_label}</span>
                  <span className="font-semibold text-forensic-fake">{formatPercent(frame.fake_probability)}</span>
                </figcaption>
              </figure>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

export default App;
