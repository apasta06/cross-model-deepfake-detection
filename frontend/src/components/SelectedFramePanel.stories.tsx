import type { Meta, StoryObj } from "@storybook/react-vite";
import { SelectedFramePanel } from "./SelectedFramePanel";
import { mockAnalysisResult } from "../mocks/analysisResult";

const meta = {
  title: "Forensics/SelectedFramePanel",
  component: SelectedFramePanel,
  args: {
    frame: mockAnalysisResult.frame_results[5],
    flaggedFrameIndices: mockAnalysisResult.flagged_frame_indices,
  },
} satisfies Meta<typeof SelectedFramePanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Flagged: Story = {};

export const LowRisk: Story = {
  args: {
    frame: mockAnalysisResult.frame_results[1],
  },
};
