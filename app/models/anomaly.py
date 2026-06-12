import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    anomaly_reason = Column(String(255), nullable=False)

    transaction = relationship("Transaction", back_populates="anomalies")

    def to_dict(self) -> dict:
        return {
            "anomaly_id": self.id,
            "transaction_id": self.transaction_id,
            "anomaly_reason": self.anomaly_reason,
        }
