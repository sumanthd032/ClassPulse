export type Level = "excellent" | "good" | "average" | "poor";

const MULTIPLIERS: Record<Level, number> = {
  excellent: 1.0,
  good: 0.75,
  average: 0.5,
  poor: 0.25,
};

export const scoreForLevel = (level: Level, maxMarks: number): number =>
  Math.round(maxMarks * MULTIPLIERS[level]);

export const levelForScore = (score: number, maxMarks: number): Level => {
  const pct = score / maxMarks;
  if (pct >= 0.9) return "excellent";
  if (pct >= 0.65) return "good";
  if (pct >= 0.4) return "average";
  return "poor";
};
