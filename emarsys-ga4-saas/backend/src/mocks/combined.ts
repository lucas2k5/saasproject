import type { CombinedReportPayload, ReportPoint, ReportSummary } from "./types";
import { emarsysReport } from "./emarsys";
import { ga4Report } from "./ga4";

const series: ReportPoint[] = emarsysReport.series.map((point, index) => {
  const ga4Point = ga4Report.series[index];
  return {
    date: point.date,
    sends: point.sends + (ga4Point?.sends ?? 0),
    opens: point.opens + (ga4Point?.opens ?? 0),
    clicks: point.clicks + (ga4Point?.clicks ?? 0),
    conversions: point.conversions + (ga4Point?.conversions ?? 0)
  };
});

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

export const combinedReport: CombinedReportPayload = {
  source: "combined",
  summary,
  series,
  updatedAt: new Date().toISOString(),
  sources: {
    emarsysUpdatedAt: emarsysReport.updatedAt,
    ga4UpdatedAt: ga4Report.updatedAt
  }
};
