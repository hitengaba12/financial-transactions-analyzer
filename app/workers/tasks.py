from datetime import datetime

from celery.utils.log import get_task_logger

from app.db.session import SessionLocal
from app.models.anomaly import Anomaly
from app.models.job import Job
from app.models.summary import Summary
from app.models.transaction import Transaction
from app.services.classification import merchant_category_map
from app.services.csv_parser import load_transactions
from app.services.summary import create_summary_payload
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="process_csv_job")
def process_csv_job(self, job_id: str, contents: str) -> None:
    session = SessionLocal()
    job = session.get(Job, job_id)
    if not job:
        logger.error("Job %s not found in Celery task", job_id)
        session.close()
        return

    job.status = "processing"
    session.commit()

    try:
        cleaned_df = load_transactions(contents)
        if cleaned_df.empty:
            raise ValueError("Parsed CSV contains no valid transactions.")

        category_updates = merchant_category_map(
            cleaned_df[cleaned_df["category"] == "Other"]["merchant"].unique().tolist()
        )
        cleaned_df.loc[
            cleaned_df["category"] == "Other", "category"
        ] = cleaned_df.loc[
            cleaned_df["category"] == "Other", "merchant"
        ].map(category_updates)

        cleaned_df["job_id"] = job.id
        transaction_records = cleaned_df.to_dict(orient="records")
        session.query(Transaction).filter(Transaction.job_id == job.id).delete()
        session.bulk_insert_mappings(Transaction, transaction_records)
        session.flush()

        from app.services.anomaly import detect_anomalies

        anomaly_rows = detect_anomalies(cleaned_df)
        anomaly_objects = [
            {"transaction_id": row["transaction_id"], "anomaly_reason": row["anomaly_reason"]}
            for row in anomaly_rows
        ]
        if anomaly_objects:
            session.bulk_insert_mappings(Anomaly, anomaly_objects)

        summary_json, category_breakdown = create_summary_payload(cleaned_df, anomaly_objects)
        summary_payload = {
            "total_spend_by_currency": summary_json["total_spend_by_currency"],
            "top_3_merchants": summary_json["top_3_merchants"],
            "anomaly_count": summary_json["anomaly_count"],
            "risk_level": summary_json["risk_level"],
            "narrative": summary_json["narrative"],
            "category_breakdown": category_breakdown,
        }
        summary = Summary(job_id=job.id, summary_json=summary_payload)
        existing_summary = session.query(Summary).filter(Summary.job_id == job.id).one_or_none()
        if existing_summary:
            existing_summary.summary_json = summary.summary_json
        else:
            session.add(summary)

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        session.commit()
    except Exception as exc:
        logger.exception("Failed to process job %s", job_id)
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        session.commit()
        raise self.retry(exc=exc, countdown=30, max_retries=1)
    finally:
        session.close()
