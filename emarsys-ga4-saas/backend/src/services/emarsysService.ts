export type EmarsysReportParams = {
  startDate: string;
  endDate: string;
};

export async function fetchEmarsysReport(_params: EmarsysReportParams) {
  // TODO: Configure Emarsys credentials in .env (e.g., EMARSYS_API_KEY).
  // TODO: Call Emarsys APIs here and map the response to the report shape.
  return null;
}
