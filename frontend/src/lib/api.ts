import type { AnalysisResult, ModelKey, ModelListResponse } from "../types/analysis";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api/v1";

async function readError(response: Response): Promise<string> {
  const payload = await response.json().catch(() => null);
  if (payload && typeof payload.detail === "string") {
    return payload.detail;
  }
  return response.statusText || "Request failed";
}

export async function getModels(): Promise<ModelListResponse> {
  const response = await fetch(`${API_BASE}/models`);
  if (!response.ok) {
    throw new Error(`Unable to load models: ${await readError(response)}`);
  }
  return response.json() as Promise<ModelListResponse>;
}

export async function analyzeMedia(file: File, model: ModelKey | string, sampleFrames: number): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("model", model);
  formData.append("sample_frames", String(sampleFrames));

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Analysis failed: ${await readError(response)}`);
  }

  return response.json() as Promise<AnalysisResult>;
}

export function reportUrl(analysisId: string, format: "html" | "json"): string {
  return `${API_BASE}/analyses/${analysisId}/report?format=${format}`;
}
