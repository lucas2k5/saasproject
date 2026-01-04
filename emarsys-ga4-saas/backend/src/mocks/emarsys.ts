import type { ReportBasePayload, ReportPoint, ReportSummary } from "./types";

const series: ReportPoint[] = [
  { date: "2024-12-23", sends: 1200, opens: 640, clicks: 190, conversions: 42 },
  { date: "2024-12-24", sends: 1500, opens: 790, clicks: 210, conversions: 55 },
  { date: "2024-12-25", sends: 1100, opens: 610, clicks: 175, conversions: 38 },
  { date: "2024-12-26", sends: 1700, opens: 930, clicks: 260, conversions: 61 },
  { date: "2024-12-27", sends: 1600, opens: 870, clicks: 245, conversions: 58 },
  { date: "2024-12-28", sends: 1850, opens: 990, clicks: 300, conversions: 72 },
  { date: "2024-12-29", sends: 1750, opens: 960, clicks: 280, conversions: 66 }
];

const totals = series.reduce(
  (acc, point) => {
    acc.sends += point.sends;
    acc.opens += point.opens;
    acc.clicks += point.clicks;
    acc.conversions += point.conversions;
    return acc;
  },
  { sends: 0, opens: 0, clicks: 0, conversions: 0 }
);

const summary: ReportSummary = {
  ...totals,
  openRate: totals.sends ? totals.opens / totals.sends : 0,
  clickRate: totals.opens ? totals.clicks / totals.opens : 0,
  conversionRate: totals.clicks ? totals.conversions / totals.clicks : 0
};

export const emarsysReport: ReportBasePayload = {
  source: "emarsys",
  summary,
  series,
  updatedAt: new Date().toISOString()
};
