import type { MultimodalPayload } from "../types/analysis";
import { formatPercent } from "../lib/format";

type MultimodalEvidenceProps = {
  payload: MultimodalPayload;
};

type FusionCode = "RVRA" | "FVRA" | "RVFA" | "FVFA";

const FUSION_LEGEND: Record<FusionCode, string> = {
  RVRA: "Real Video + Real Audio",
  FVRA: "Fake Video + Real Audio",
  RVFA: "Real Video + Fake Audio",
  FVFA: "Fake Video + Fake Audio",
};

const FUSION_CODES = Object.keys(FUSION_LEGEND) as FusionCode[];

// Backend emits full strings like "Fake Video & Real Audio (FVRA)".
// Audio-missing case emits "Video Analysis (Audio Missing/Degraded)" -> no code.
function parseFusionCode(classification: string): FusionCode | null {
  const match = classification.match(/\(([A-Z]{4})\)/);
  if (match && (FUSION_CODES as string[]).includes(match[1])) {
    return match[1] as FusionCode;
  }
  return null;
}

function thresholdPercentLabel(threshold: number): string {
  return `Threshold: ${(threshold * 100).toFixed(0)}%`;
}

const scoreTone = (isFake: boolean): string =>
  isFake
    ? "border-forensic-fake/50 text-forensic-fake"
    : "border-forensic-real/40 text-forensic-real";

export function MultimodalEvidence({ payload }: MultimodalEvidenceProps) {
  const videoIsFake = payload.video_score > payload.video_threshold;
  const hasAudio = payload.audio_available && payload.audio_score != null;
  const audioIsFake = hasAudio && (payload.audio_score as number) > payload.audio_threshold;
  const fusionCode = parseFusionCode(payload.classification);

  return (
    <section className="grid gap-3 md:grid-cols-3" aria-label="Multimodal evidence">
      <article className={`rounded-2xl border bg-forensic-panel/80 p-4 backdrop-blur ${scoreTone(videoIsFake)}`}>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Visual analysis</p>
        <p className="mt-2 text-2xl font-bold">{formatPercent(payload.video_score)}</p>
        <p className="mt-1 text-xs text-forensic-muted">{thresholdPercentLabel(payload.video_threshold)}</p>
        <p className="mt-2 text-xs font-medium">{videoIsFake ? "Above threshold - suspicious" : "Within authentic range"}</p>
      </article>

      {hasAudio ? (
        <article className={`rounded-2xl border bg-forensic-panel/80 p-4 backdrop-blur ${scoreTone(audioIsFake)}`}>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Audio analysis</p>
          <p className="mt-2 text-2xl font-bold">{formatPercent(payload.audio_score as number)}</p>
          <p className="mt-1 text-xs text-forensic-muted">{thresholdPercentLabel(payload.audio_threshold)}</p>
          <p className="mt-2 text-xs font-medium">{audioIsFake ? "Above threshold - suspicious" : "Within authentic range"}</p>
        </article>
      ) : (
        <article className="rounded-2xl border border-forensic-border bg-forensic-panel/60 p-4 backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Audio analysis</p>
          <p className="mt-2 text-base font-semibold text-forensic-muted">No audio track detected</p>
          <p className="mt-1 text-xs text-forensic-muted">Result used visual-only fallback.</p>
        </article>
      )}

      <article className="rounded-2xl border border-forensic-border bg-forensic-panel/80 p-4 backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-forensic-muted">Fusion result</p>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {fusionCode ? (
            <span className="rounded-full border border-sky-300/40 bg-sky-950/70 px-2.5 py-1 text-sm font-bold text-sky-100">{fusionCode}</span>
          ) : null}
          <p className="text-sm font-semibold text-white">{payload.classification}</p>
        </div>
        {payload.fused_score != null ? (
          <p className="mt-2 text-xs text-forensic-muted">Fused suspiciousness: {formatPercent(payload.fused_score)}</p>
        ) : null}
        <dl className="mt-3 space-y-1 border-t border-white/10 pt-2 text-xs text-forensic-muted">
          {FUSION_CODES.map((code) => (
            <div key={code} className="flex justify-between gap-3">
              <dt className={`font-semibold ${code === fusionCode ? "text-white" : ""}`}>{code}</dt>
              <dd className={code === fusionCode ? "text-white" : ""}>{FUSION_LEGEND[code]}</dd>
            </div>
          ))}
        </dl>
      </article>
    </section>
  );
}
