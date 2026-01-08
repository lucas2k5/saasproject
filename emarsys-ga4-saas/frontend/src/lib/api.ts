import type { ReportPayload } from "../types/reports";
import { supabaseClient } from "./supabaseClient";

export type ReportSource = "combined" | "emarsys" | "ga4";

export async function fetchReport(source: ReportSource): Promise<ReportPayload> {
  const token = supabaseClient
    ? (await supabaseClient.auth.getSession()).data.session?.access_token
    : null;

  const response = await fetch(`/api/reports/${source}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  });
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json() as Promise<ReportPayload>;
}
