import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import admin, auth, control, data, sites
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
import app.state as app_state
from app.workers.scheduler import start_scheduler, stop_scheduler
from scripts.bootstrap_admin import run as bootstrap_admin

logger = logging.getLogger(__name__)

_DB_RETRY_DELAY = 5  # seconds


async def _init_db_with_retry() -> None:
    attempt = 0
    while True:
        attempt += 1
        try:
            # Run all blocking synchronous DB operations in a thread so the
            # event loop (and therefore the HTTP server) is never frozen while
            # waiting for the database to respond.
            await asyncio.to_thread(Base.metadata.create_all, bind=engine)
            try:
                await asyncio.to_thread(ensure_schema_compatibility)
            except Exception as compat_exc:
                logger.warning("Schema compatibility check failed (non-fatal): %s", compat_exc)
            await asyncio.to_thread(bootstrap_admin)
            app_state.db_ready = True
            if settings.scheduler_enabled:
                try:
                    start_scheduler()
                except Exception as sched_exc:
                    logger.warning("Scheduler failed to start: %s", sched_exc)
            logger.info("Database initialised successfully.")
            return
        except Exception as exc:
            logger.warning(
                "Database not ready (attempt %d): %s – retrying in %ds…",
                attempt,
                exc,
                _DB_RETRY_DELAY,
            )
            await asyncio.sleep(_DB_RETRY_DELAY)


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

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(sites.router, prefix=settings.api_v1_prefix)
app.include_router(data.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
app.include_router(control.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    if not app_state.db_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "starting", "db_ready": False},
        )
    return {"status": "ok", "db_ready": True}


# Serve the built React frontend (present in production image at /app/static)
_static_dir = Path("/app/static")
if _static_dir.is_dir():
    _assets_dir = _static_dir / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="static-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str) -> FileResponse:
        return FileResponse(str(_static_dir / "index.html"))
