from fastapi import FastAPI

from app.api.routes import router
from app.utils.logger import setup_logging
from app.utils.settings import settings

setup_logging()

app = FastAPI(
    title="Financial Transactions Analyzer",
    description="API for CSV transaction ingestion, anomaly detection, merchant classification, and summary reporting.",
    version="1.0.0",
)
app.include_router(router)


@app.get("/healthz")
def health_check() -> dict:
    return {"status": "ok", "service": "financial-transactions-analyzer"}
