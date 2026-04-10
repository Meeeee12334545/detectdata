from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(subject=user.username)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserProfile)
def me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile(user_id=current_user.user_id, username=current_user.username, role=current_user.role.value)
