import type { RiskKey } from "../types/analysis";

export const riskToneByKey: Record<RiskKey, string> = {
  likely_real: "border-forensic-real/40 text-forensic-real",
  uncertain: "border-forensic-uncertain/40 text-forensic-uncertain",
  likely_fake: "border-forensic-fake/50 text-forensic-fake",
};

export const riskChipByKey: Record<RiskKey, string> = {
  likely_real: "border-forensic-real/35 bg-forensic-real/10 text-emerald-100",
  uncertain: "border-forensic-uncertain/35 bg-forensic-uncertain/10 text-amber-100",
  likely_fake: "border-forensic-fake/35 bg-forensic-fake/10 text-red-100",
};

export function isFlaggedFrame(frameIndex: number, flaggedFrameIndices: number[]): boolean {
  return flaggedFrameIndices.includes(frameIndex);
}
