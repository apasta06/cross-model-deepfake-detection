import type { AnalysisResult, FrameResult, RiskKey } from "../types/analysis";

const riskForProbability = (probability: number): { risk_key: RiskKey; risk_label: FrameResult["risk_label"] } => {
  if (probability <= 0.35) {
    return { risk_key: "likely_real", risk_label: "Likely Real" };
  }
  if (probability <= 0.74) {
    return { risk_key: "uncertain", risk_label: "Uncertain" };
  }
  return { risk_key: "likely_fake", risk_label: "Likely Fake" };
};

const probabilities = [0.18, 0.23, 0.41, 0.66, 0.79, 0.91, 0.87, 0.72, 0.58, 0.34, 0.28, 0.21];
const thumbnailThemes = ["0f172a/38bdf8", "111827/a78bfa", "1e293b/f97316", "172554/facc15", "450a0a/fca5a5", "7f1d1d/fecaca"];

const frameResults: FrameResult[] = probabilities.map((fake_probability, index) => ({
  frame_index: index * 42,
  timestamp_seconds: index * 1.8,
  timestamp_label: `00:${String(Math.round(index * 1.8)).padStart(2, "0")}`,
  fake_probability,
  ...riskForProbability(fake_probability),
  thumbnail_url: `https://placehold.co/640x360/${thumbnailThemes[index % thumbnailThemes.length]}?text=Evidence+Frame+${index + 1}`,
}));

export const mockAnalysisResult: AnalysisResult = {
  analysis_id: "demo-fake-001",
  input_type: "video",
  filename: "interview_clip_sample.mp4",
  filesize: 48_700_000,
  verdict: "PARTIAL FORGERY (Visual Identity Swap)",
  confidence_score: 0.57,
  risk_level: "uncertain",
  summary_text: "Fake Video & Real Audio (FVRA). Visual suspiciousness 82.0%, audio suspiciousness 32.0%, fused suspiciousness 57.0%.",
  flagged_frame_indices: frameResults.filter((frame) => frame.fake_probability >= 0.65).map((frame) => frame.frame_index),
  frame_stats: {
    sampled_frames: frameResults.length,
    fake_frames: frameResults.filter((frame) => frame.risk_key === "likely_fake").length,
    uncertain_frames: frameResults.filter((frame) => frame.risk_key === "uncertain").length,
    real_frames: frameResults.filter((frame) => frame.risk_key === "likely_real").length,
    avg_fake_probability: 0.52,
  },
  evidence_paths: [
    {
      label: "Uploaded media review",
      kind: "viewer",
      description: "The submitted clip is loaded in the forensic viewer with duration, resolution, and extracted-frame metadata.",
    },
    {
      label: "Frame-level model timeline",
      kind: "timeline",
      description: "Sampled frames are shown with per-frame fake probabilities for quick triage.",
    },
    {
      label: "Audit report package",
      kind: "report",
      description: "Verdict summary, flagged timestamps, and frame evidence are ready for export.",
    },
  ],
  created_at: "2026-05-17T12:00:00Z",
  model_used: "MULTIMODAL_EFFICIENTB0",
  media_metadata: {
    filename: "interview_clip_sample.mp4",
    filesize: 48_700_000,
    extension: ".mp4",
    media_kind: "video",
    duration_seconds: 21.6,
    fps: 24,
    frame_count: 518,
    width: 1920,
    height: 1080,
  },
  frame_results: frameResults,
  warnings: [],
  report_payload: {
    classification: "Fake Video & Real Audio (FVRA)",
    alert_level: "PARTIAL FORGERY (Visual Identity Swap)",
    video_score: 0.82,
    audio_score: 0.32,
    fused_score: 0.57,
    video_threshold: 0.6,
    audio_threshold: 0.5,
    audio_available: true,
    sampled_visual_frames: frameResults.length,
    model_family: "EfficientNet-B0 multimodal",
  },
};
