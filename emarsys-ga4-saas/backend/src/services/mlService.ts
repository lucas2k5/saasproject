import axios from "axios";

const mlBaseUrl = process.env.ML_SERVICE_URL || "http://localhost:8001";

export type EngagementPredictionRequest = {
  customerId: string;
  features: Record<string, unknown>;
};

export type EngagementPredictionResponse = {
  score: number;
  segment: string;
};

export async function predictEngagement(
  payload: EngagementPredictionRequest
): Promise<EngagementPredictionResponse> {
  const response = await axios.post(`${mlBaseUrl}/predict/engagement`, {
    customer_id: payload.customerId,
    features: payload.features
  });

  return response.data as EngagementPredictionResponse;
}
