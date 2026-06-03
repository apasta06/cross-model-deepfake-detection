import type { Meta, StoryObj } from "@storybook/react-vite";
import { ForensicMediaViewer } from "./ForensicMediaViewer";
import { mockAnalysisResult } from "../mocks/analysisResult";

const meta = {
  title: "Forensics/ForensicMediaViewer",
  component: ForensicMediaViewer,
  args: {
    result: mockAnalysisResult,
    selectedFrame: mockAnalysisResult.frame_results[5],
    mediaPreviewUrl: null,
    showHeatmap: false,
    onToggleHeatmap: () => {},
  },
} satisfies Meta<typeof ForensicMediaViewer>;

export default meta;
type Story = StoryObj<typeof meta>;

// Default: no heatmap shown. Media preview is null here (Storybook has no
// uploaded file), so the "preview unavailable" panel renders; the toggle and
// metadata strip are still exercised.
export const Default: Story = {};

// Heatmap toggled on, selected frame carries heatmap + face_box data.
// Note: the overlay itself only paints over a real <video> element once it is
// paused and aligned; with a null preview the toggle state and caption render.
export const WithHeatmap: Story = {
  args: {
    selectedFrame: mockAnalysisResult.frame_results[5],
    showHeatmap: true,
  },
};

// Heatmap toggled on, but the selected frame has no heatmap (face_box null) —
// exercises the "Heatmap unavailable for this frame" message path.
export const HeatmapUnavailableFrame: Story = {
  args: {
    selectedFrame: mockAnalysisResult.frame_results[1],
    showHeatmap: true,
  },
};
