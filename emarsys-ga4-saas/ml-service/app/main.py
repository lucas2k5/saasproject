from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="KeepAIS ML Service")


class EngagementRequest(BaseModel):
    customer_id: str
    features: Dict[str, Any]


class EngagementResponse(BaseModel):
    score: float
    segment: str


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ml-service"}


@app.post("/predict/engagement", response_model=EngagementResponse)
async def predict_engagement(payload: EngagementRequest):
    # Mocked prediction for now. Replace with real model inference later.
    score = 0.78
    segment = "high"
    return {"score": score, "segment": segment}
