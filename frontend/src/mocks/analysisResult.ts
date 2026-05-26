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

const frameResults: FrameResult[] = probabilities.map((fake_probability, index) => ({
  frame_index: index * 42,
  timestamp_seconds: index * 1.8,
  timestamp_label: `00:${String(Math.round(index * 1.8)).padStart(2, "0")}`,
  fake_probability,
  ...riskForProbability(fake_probability),
  thumbnail_url: `https://placehold.co/320x180/111827/f3f4f6?text=Frame+${index + 1}`,
}));

export const mockAnalysisResult: AnalysisResult = {
  analysis_id: "demo-fake-001",
  input_type: "video",
  filename: "interview_clip_sample.mp4",
  filesize: 48_700_000,
  verdict: "Likely Fake",
  confidence_score: 0.89,
  risk_level: "likely_fake",
  summary_text: "Likely manipulated. Four sampled frames crossed the warning threshold, concentrated around the middle of the clip.",
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
      label: "Video review",
      kind: "viewer",
      description: "The original uploaded media is available in the forensic viewer for manual review.",
    },
    {
      label: "Frame timeline",
      kind: "timeline",
      description: "Sampled frames are shown with per-frame fake probabilities for quick triage.",
    },
  ],
  created_at: "2026-05-17T12:00:00Z",
  model_used: "MESO4",
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
  warnings: ["Mock result: thumbnails and model output are fixture data until the FastAPI backend is connected."],
  report_payload: {
    source: "frontend mock fixture",
  },
};
