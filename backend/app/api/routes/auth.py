import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import app.state as app_state
from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile


router = APIRouter(prefix="/auth", tags=["auth"])

_DB_WAIT_SECONDS = 25


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    # If the database is still initialising (e.g. cold start), wait for it
    # rather than immediately returning 503. The event loop stays free because
    # _init_db_with_retry now runs its blocking work in a thread.
    if not app_state.db_ready:
        for _ in range(_DB_WAIT_SECONDS):
            await asyncio.sleep(1)
            if app_state.db_ready:
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is starting up, please try again in a moment",
            )
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(subject=user.username)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserProfile)
def me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile(user_id=current_user.user_id, username=current_user.username, role=current_user.role.value)
