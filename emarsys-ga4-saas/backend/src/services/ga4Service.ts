export type Ga4ReportParams = {
  propertyId: string;
  startDate: string;
  endDate: string;
};

export async function fetchGa4Report(_params: Ga4ReportParams) {
  // TODO: Configure GA4 credentials in .env (e.g., GA4_CLIENT_EMAIL, GA4_PRIVATE_KEY).
  // TODO: Call GA4 Reporting API here and map the response to the report shape.
  return null;
}
