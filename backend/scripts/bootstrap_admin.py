from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import Role, User
from app.db.session import SessionLocal, engine


DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == DEFAULT_USERNAME).first()
        if existing:
            print("Admin already exists")
            return

        admin = User(
            username=DEFAULT_USERNAME,
            password_hash=get_password_hash(DEFAULT_PASSWORD),
            role=Role.admin,
        )
        db.add(admin)
        db.commit()
        print("Created default admin user: admin / admin123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
