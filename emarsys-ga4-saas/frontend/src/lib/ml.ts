import { supabaseClient } from "./supabaseClient";

export type EngagementPrediction = {
  score: number;
  segment: string;
};

export async function fetchEngagementPrediction(
  customerId: string,
  features: Record<string, unknown>
): Promise<EngagementPrediction> {
  const authDisabled = import.meta.env.VITE_AUTH_DISABLED === "true";
  const token = supabaseClient
    ? (await supabaseClient.auth.getSession()).data.session?.access_token
    : null;

  if (!token && !authDisabled) {
    throw new Error("Missing access token");
  }

  const response = await fetch("/api/ml/engagement", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ customerId, features })
  });

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return response.json() as Promise<EngagementPrediction>;
}
