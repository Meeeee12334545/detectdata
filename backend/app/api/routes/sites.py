from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.models import Site, User
from app.db.session import get_db
from app.schemas.site import SiteCreate, SiteResponse


router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteResponse])
def list_sites(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SiteResponse]:
    return db.query(Site).order_by(Site.site_name.asc()).all()


@router.post("", response_model=SiteResponse)
def create_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SiteResponse:
    if payload.pmac_code:
        existing = db.query(Site).filter(Site.pmac_code == payload.pmac_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="PMAC already exists")

    site = Site(**payload.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)
    return site
