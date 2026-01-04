import type { ReportBasePayload, ReportPoint, ReportSummary } from "./types";

const series: ReportPoint[] = [
  { date: "2024-12-23", sends: 900, opens: 520, clicks: 160, conversions: 34 },
  { date: "2024-12-24", sends: 980, opens: 560, clicks: 170, conversions: 36 },
  { date: "2024-12-25", sends: 870, opens: 490, clicks: 150, conversions: 31 },
  { date: "2024-12-26", sends: 1120, opens: 640, clicks: 190, conversions: 45 },
  { date: "2024-12-27", sends: 1080, opens: 610, clicks: 185, conversions: 43 },
  { date: "2024-12-28", sends: 1200, opens: 700, clicks: 220, conversions: 52 },
  { date: "2024-12-29", sends: 1150, opens: 680, clicks: 210, conversions: 49 }
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

export const ga4Report: ReportBasePayload = {
  source: "ga4",
  summary,
  series,
  updatedAt: new Date().toISOString()
};
