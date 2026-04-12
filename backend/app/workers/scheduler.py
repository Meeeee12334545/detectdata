from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.db.models import PollingConfig
from app.db.session import SessionLocal
from app.services.ingestion import IngestionService


scheduler = BackgroundScheduler()
_service = IngestionService()


def run_sync_job() -> None:
    db: Session = SessionLocal()
    try:
        _service.sync_all(db)
    finally:
        db.close()


def configure_scheduler() -> None:
    db: Session = SessionLocal()
    try:
        configs = db.query(PollingConfig).filter(PollingConfig.is_enabled.is_(True)).all()
    finally:
        db.close()

    scheduler.remove_all_jobs()

    if not configs:
        scheduler.add_job(
            run_sync_job,
            "interval",
            minutes=5,
            id="default-sync",
            replace_existing=True,
            next_run_time=datetime.utcnow(),
        )
        return

    for cfg in configs:
        job_id = f"sync-{cfg.id}"
        scheduler.add_job(
            run_sync_job,
            "interval",
            minutes=max(cfg.frequency_minutes, 1),
            id=job_id,
            replace_existing=True,
            next_run_time=datetime.utcnow(),
        )


def start_scheduler() -> None:
    configure_scheduler()
    if not scheduler.running:
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
