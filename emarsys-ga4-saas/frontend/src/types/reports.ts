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

export type BaseReport = {
  source: "emarsys" | "ga4";
  summary: ReportSummary;
  series: ReportPoint[];
  updatedAt: string;
};

export type CombinedReport = {
  source: "combined";
  summary: ReportSummary;
  series: ReportPoint[];
  updatedAt: string;
  sources: {
    emarsysUpdatedAt: string;
    ga4UpdatedAt: string;
  };
};

export type ReportPayload = BaseReport | CombinedReport;
