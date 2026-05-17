import type { Meta, StoryObj } from "@storybook/react-vite";
import { FrameThumbnailStrip } from "./FrameThumbnailStrip";
import { mockAnalysisResult } from "../mocks/analysisResult";

const meta = {
  title: "Forensics/FrameThumbnailStrip",
  component: FrameThumbnailStrip,
  args: {
    frames: mockAnalysisResult.frame_results,
    flaggedFrameIndices: mockAnalysisResult.flagged_frame_indices,
    selectedFrameIndex: mockAnalysisResult.frame_results[0].frame_index,
    onSelectFrame: () => {},
  },
} satisfies Meta<typeof FrameThumbnailStrip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const SelectedFlaggedFrame: Story = {
  args: {
    selectedFrameIndex: mockAnalysisResult.flagged_frame_indices[0],
  },
};
