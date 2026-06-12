from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.anomaly import Anomaly
from app.models.summary import Summary
from app.schemas.job import (
    JobCreateResponse,
    JobResultResponse,
    JobStatusResponse,
    ListJobsResponse,
)
from app.workers.tasks import process_csv_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/upload", response_model=JobCreateResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> JobCreateResponse:
    if file.content_type not in {"text/csv", "application/vnd.ms-excel", "application/csv"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must be a CSV.")

    payload = await file.read()
    contents = payload.decode("utf-8", errors="ignore")
    job = Job(status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    process_csv_job.delay(job.id, contents)

    return JobCreateResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)) -> JobStatusResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return JobStatusResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}/results", response_model=JobResultResponse)
def get_job_results(job_id: str, db: Session = Depends(get_db)) -> JobResultResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    transactions = (
        db.query(Transaction)
        .filter(Transaction.job_id == job.id)
        .order_by(Transaction.date)
        .all()
    )
    anomalies = (
        db.query(Anomaly)
        .join(Transaction)
        .filter(Transaction.job_id == job.id)
        .all()
    )
    summary = db.query(Summary).filter(Summary.job_id == job.id).one_or_none()
    summary_json = summary.summary_json if summary else {}

    return JobResultResponse(
        transactions=[t.to_dict() for t in transactions],
        anomalies=[a.to_dict() for a in anomalies],
        category_breakdown=summary_json.get("category_breakdown", {}),
        summary=summary_json,
    )


@router.get("", response_model=ListJobsResponse)
def list_jobs(db: Session = Depends(get_db)) -> ListJobsResponse:
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return ListJobsResponse(jobs=[job.to_dict() for job in jobs])
