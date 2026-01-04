export type ReportPoint = {
  date: string;
  sends: number;
  opens: number;
  clicks: number;
  conversions: number;
};

export type ReportSummary = {
  sends: number;
  opens: number;
  clicks: number;
  conversions: number;
  openRate: number;
  clickRate: number;
  conversionRate: number;
};

export type ReportBasePayload = {
  source: "emarsys" | "ga4" | "combined";
  summary: ReportSummary;
  series: ReportPoint[];
  updatedAt: string;
};

export type CombinedReportPayload = ReportBasePayload & {
  source: "combined";
  sources: {
    emarsysUpdatedAt: string;
    ga4UpdatedAt: string;
  };
};
