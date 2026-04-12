from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def _build_engine():
    url = settings.database_url
    parsed = make_url(url)
    if parsed.drivername.startswith("sqlite"):
        # SQLite does not support connect_timeout; check_same_thread=False is
        # required for multi-threaded use (e.g. background scheduler).
        return create_engine(url, future=True, connect_args={"check_same_thread": False})
    return create_engine(url, future=True, pool_pre_ping=True, connect_args={"connect_timeout": 10})


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
