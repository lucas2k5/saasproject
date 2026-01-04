import type { ReportPayload } from "../types/reports";

export type ReportSource = "combined" | "emarsys" | "ga4";

export async function fetchReport(source: ReportSource): Promise<ReportPayload> {
  const response = await fetch(`/api/reports/${source}`);
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json() as Promise<ReportPayload>;
}
