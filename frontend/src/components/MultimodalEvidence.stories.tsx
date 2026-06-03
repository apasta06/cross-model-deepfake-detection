import type { Meta, StoryObj } from "@storybook/react-vite";
import { MultimodalEvidence } from "./MultimodalEvidence";
import { mockAnalysisResult } from "../mocks/analysisResult";
import type { MultimodalPayload } from "../types/analysis";

const basePayload = mockAnalysisResult.report_payload as MultimodalPayload;

const meta = {
  title: "Forensics/MultimodalEvidence",
  component: MultimodalEvidence,
  args: {
    payload: basePayload,
  },
} satisfies Meta<typeof MultimodalEvidence>;

export default meta;
type Story = StoryObj<typeof meta>;

export const FakeVideoRealAudio: Story = {};

export const TotalSynthesis: Story = {
  args: {
    payload: {
      ...basePayload,
      classification: "Fake Video & Fake Audio (FVFA)",
      alert_level: "TOTAL MULTIMODAL SYNTHESIS",
      video_score: 0.91,
      audio_score: 0.83,
      fused_score: 0.87,
    },
  },
};

export const AudioMissing: Story = {
  args: {
    payload: {
      ...basePayload,
      classification: "Video Analysis (Audio Missing/Degraded)",
      alert_level: "FAKE",
      audio_score: null,
      audio_available: false,
      fused_score: basePayload.video_score,
    },
  },
};
