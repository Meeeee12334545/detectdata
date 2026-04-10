from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.models import User
from app.db.session import get_db
from app.services.ingestion import IngestionService
from app.workers.scheduler import start_scheduler, stop_scheduler


router = APIRouter(prefix="/control", tags=["control"])
_service = IngestionService()


@router.post("/sync-now")
def sync_now(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    return _service.sync_all(db)


@router.post("/backfill")
def backfill(
    days_back: int = 3650,
    chunk_days: int = 90,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    return _service.backfill_all(db, days_back=days_back, chunk_days=chunk_days)


@router.post("/start")
def start(
    _: User = Depends(require_admin),
) -> dict:
    start_scheduler()
    return {"status": "started"}


@router.post("/stop")
def stop(
    _: User = Depends(require_admin),
) -> dict:
    stop_scheduler()
    return {"status": "stopped"}
