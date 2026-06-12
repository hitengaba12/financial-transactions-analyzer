from fastapi import APIRouter

router = APIRouter()

from app.api import routes  # noqa: F401
