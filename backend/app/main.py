from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import admin, auth, control, data, sites
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.workers.scheduler import start_scheduler, stop_scheduler


def ensure_schema_compatibility() -> None:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE sites ADD COLUMN IF NOT EXISTS pmac_code VARCHAR(4)"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()
    if settings.scheduler_enabled:
        start_scheduler()
    try:
        yield
    finally:
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
    return {"status": "ok"}
