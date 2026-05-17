import type { Meta, StoryObj } from "@storybook/react-vite";
import { VerdictHero } from "./VerdictHero";
import { mockAnalysisResult } from "../mocks/analysisResult";

const meta = {
  title: "Forensics/VerdictHero",
  component: VerdictHero,
  args: {
    result: mockAnalysisResult,
  },
} satisfies Meta<typeof VerdictHero>;

export default meta;
type Story = StoryObj<typeof meta>;

export const LikelyFake: Story = {};

export const Uncertain: Story = {
  args: {
    result: { ...mockAnalysisResult, verdict: "Uncertain", risk_level: "uncertain", confidence_score: 0.62 },
  },
};
