import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.routes import admin, auth, control, data, sites
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.workers.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)

_DB_RETRY_ATTEMPTS = 10
_DB_RETRY_DELAY = 5  # seconds

# Tracks whether the database has been successfully initialised.
db_ready: bool = False


async def _init_db_with_retry() -> None:
    global db_ready
    try:
        for attempt in range(1, _DB_RETRY_ATTEMPTS + 1):
            try:
                Base.metadata.create_all(bind=engine)
                ensure_schema_compatibility()
                db_ready = True
                if settings.scheduler_enabled:
                    start_scheduler()
                logger.info("Database initialised successfully.")
                return
            except OperationalError as exc:
                if attempt == _DB_RETRY_ATTEMPTS:
                    logger.error(
                        "Database not ready after %d attempts – giving up: %s",
                        _DB_RETRY_ATTEMPTS,
                        exc,
                    )
                    return
                logger.warning(
                    "Database not ready (attempt %d/%d): %s – retrying in %ds…",
                    attempt,
                    _DB_RETRY_ATTEMPTS,
                    exc,
                    _DB_RETRY_DELAY,
                )
                await asyncio.sleep(_DB_RETRY_DELAY)
    except Exception:
        logger.exception("Unexpected error during database initialisation.")


def ensure_schema_compatibility() -> None:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE sites ADD COLUMN IF NOT EXISTS pmac_code VARCHAR(4)"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Run DB initialisation in the background so the HTTP server can bind its
    # port immediately.  Render (and other platforms) need a listening port
    # before they consider the deployment healthy.
    db_init_task = asyncio.create_task(_init_db_with_retry())
    try:
        yield
    finally:
        db_init_task.cancel()
        stop_scheduler()


app = FastAPI(title=settings.project_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(sites.router, prefix=settings.api_v1_prefix)
app.include_router(data.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
app.include_router(control.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "db_ready": db_ready}
