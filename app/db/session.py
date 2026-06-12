import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.settings import settings

engine = create_engine(str(settings.database_url), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
