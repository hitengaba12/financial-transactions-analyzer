from typing import Dict, List

from pydantic import BaseModel


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str


class TransactionResponse(BaseModel):
    transaction_id: str
    job_id: str
    account_id: str
    date: str
    merchant: str
    amount: float
    currency: str
    category: str
    status: str


class AnomalyResponse(BaseModel):
    anomaly_id: str
    transaction_id: str
    anomaly_reason: str


class JobResultResponse(BaseModel):
    transactions: List[TransactionResponse]
    anomalies: List[AnomalyResponse]
    category_breakdown: Dict[str, int]
    summary: Dict[str, object]


class JobListItemResponse(BaseModel):
    job_id: str
    status: str
    created_at: str | None = None
    completed_at: str | None = None


class ListJobsResponse(BaseModel):
    jobs: List[JobListItemResponse]
