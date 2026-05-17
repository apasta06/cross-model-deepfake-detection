import type { Meta, StoryObj } from "@storybook/react-vite";
import { FrameRiskTimeline } from "./FrameRiskTimeline";
import { mockAnalysisResult } from "../mocks/analysisResult";

const meta = {
  title: "Forensics/FrameRiskTimeline",
  component: FrameRiskTimeline,
  args: {
    frames: mockAnalysisResult.frame_results,
    flaggedFrameIndices: mockAnalysisResult.flagged_frame_indices,
    selectedFrameIndex: mockAnalysisResult.frame_results[0].frame_index,
    onSelectFrame: () => {},
  },
} satisfies Meta<typeof FrameRiskTimeline>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
