export type RiskKey = "likely_real" | "uncertain" | "likely_fake";

export type ModelKey = "MULTIMODAL_EFFICIENTB0";

export type ModelInfo = {
  key: ModelKey;
  description: string;
};

export type ModelListResponse = {
  models: ModelInfo[];
};

export type MediaMetadata = {
  filename: string;
  filesize: number;
  extension: string;
  media_kind: "video" | "image";
  duration_seconds?: number | null;
  fps?: number | null;
  frame_count?: number | null;
  width?: number | null;
  height?: number | null;
};

export type EvidenceAsset = {
  label: string;
  kind: string;
  path?: string | null;
  description: string;
};

export type FrameResult = {
  frame_index: number;
  timestamp_seconds: number;
  timestamp_label: string;
  fake_probability: number;
  risk_label: "Likely Real" | "Uncertain" | "Likely Fake";
  risk_key: RiskKey;
  thumbnail_url?: string | null;
  heatmap_url?: string | null;
  face_box?: [number, number, number, number] | null;
  frame_width?: number | null;
  frame_height?: number | null;
};

export type MultimodalPayload = {
  classification: string;
  alert_level?: string;
  video_score: number;
  audio_score: number | null;
  fused_score?: number;
  video_threshold: number;
  audio_threshold: number;
  audio_available: boolean;
  sampled_visual_frames?: number;
  model_family?: string;
  warnings?: string[];
};

export type FrameStats = {
  sampled_frames: number;
  fake_frames: number;
  uncertain_frames: number;
  real_frames: number;
  avg_fake_probability: number;
};

export type AnalysisResult = {
  analysis_id: string;
  input_type: "video" | "image";
  filename: string;
  filesize: number;
  verdict: string;
  confidence_score: number;
  risk_level: RiskKey;
  summary_text: string;
  flagged_frame_indices: number[];
  frame_stats: FrameStats;
  evidence_paths: EvidenceAsset[];
  created_at: string;
  model_used: ModelKey | string;
  media_metadata: MediaMetadata;
  frame_results: FrameResult[];
  warnings: string[];
  report_payload?: MultimodalPayload;
};

export type HistoryRecord = {
  analysis_id: string;
  created_at: string;
  filename: string;
  filesize: number;
  input_type: "video" | "image";
  model_used: string;
  verdict: string;
  confidence_score: number;
  risk_level: string;
  summary_text: string;
  report_path?: string | null;
};
