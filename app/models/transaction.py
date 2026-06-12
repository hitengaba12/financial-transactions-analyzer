import uuid
from datetime import date

from sqlalchemy import Column, Date, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(128), nullable=False)
    date = Column(Date, nullable=False)
    merchant = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False)
    category = Column(String(64), nullable=False, default="Other")
    status = Column(String(32), nullable=False)

    job = relationship("Job", back_populates="transactions")
    anomalies = relationship("Anomaly", back_populates="transaction", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.id,
            "job_id": self.job_id,
            "account_id": self.account_id,
            "date": self.date.isoformat() if self.date else None,
            "merchant": self.merchant,
            "amount": self.amount,
            "currency": self.currency,
            "category": self.category,
            "status": self.status,
        }
