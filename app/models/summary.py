import uuid

from sqlalchemy import Column, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    summary_json = Column(JSON, nullable=False)

    job = relationship("Job", back_populates="summary")
