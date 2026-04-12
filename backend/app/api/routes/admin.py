from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.security import get_password_hash
from app.db.models import (
    Channel,
    ChannelAdminSetting,
    Device,
    IngestionJobLog,
    PollingConfig,
    Role,
    Site,
    SiteHydraulicConfig,
    User,
)
from app.db.session import get_db


router = APIRouter(prefix="/admin", tags=["admin"])


class UserCreate(BaseModel):
    username: str
    password: str
    role: Role = Role.user


class PollingConfigUpsert(BaseModel):
    site_id: int | None = None
    device_id: int | None = None
    frequency_minutes: int = 5
    is_enabled: bool = True


class ChannelVisibilityItem(BaseModel):
    channel_id: int
    is_viewable: bool = True
    display_name: str | None = None


class ChannelVisibilityUpdate(BaseModel):
    items: list[ChannelVisibilityItem]


class HydraulicConfigUpdate(BaseModel):
    enabled: bool = False
    pipe_shape: str = "circular"
    depth_channel_id: int | None = None
    velocity_channel_id: int | None = None
    flow_channel_id: int | None = None
    diameter_m: float | None = None
    width_m: float | None = None
    height_m: float | None = None
    output_units: str = "L/s"


@router.post("/users")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.user_id, "username": user.username, "role": user.role.value}


@router.post("/polling-configs")
def upsert_polling_config(
    payload: PollingConfigUpsert,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    cfg = PollingConfig(
        site_id=payload.site_id,
        device_id=payload.device_id,
        frequency_minutes=max(payload.frequency_minutes, 1),
        is_enabled=payload.is_enabled,
    )
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return {"id": cfg.id, "frequency_minutes": cfg.frequency_minutes, "is_enabled": cfg.is_enabled}


@router.get("/sites/{site_id}/channels")
def get_site_channels(
    site_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    site = db.query(Site).filter(Site.site_id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    rows = (
        db.query(Channel, Device, ChannelAdminSetting)
        .join(Device, Device.device_id == Channel.device_id)
        .outerjoin(
            ChannelAdminSetting,
            (ChannelAdminSetting.channel_id == Channel.channel_id) & (ChannelAdminSetting.site_id == site_id),
        )
        .filter(Device.site_id == site_id)
        .order_by(Device.device_name.asc(), Channel.parameter.asc())
        .all()
    )

    return {
        "site": {"site_id": site.site_id, "site_name": site.site_name, "pmac_code": site.pmac_code},
        "channels": [
            {
                "channel_id": c.channel_id,
                "device_name": d.device_name,
                "parameter": c.parameter,
                "units": c.units,
                "is_viewable": s.is_viewable if s else True,
                "display_name": s.display_name if s else None,
            }
            for (c, d, s) in rows
        ],
    }


@router.post("/sites/{site_id}/channels/visibility")
def update_channel_visibility(
    site_id: int,
    payload: ChannelVisibilityUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    updated = 0
    for item in payload.items:
        setting = (
            db.query(ChannelAdminSetting)
            .filter(ChannelAdminSetting.site_id == site_id, ChannelAdminSetting.channel_id == item.channel_id)
            .first()
        )
        if not setting:
            setting = ChannelAdminSetting(site_id=site_id, channel_id=item.channel_id)
            db.add(setting)

        setting.is_viewable = item.is_viewable
        setting.display_name = item.display_name
        updated += 1

    db.commit()
    return {"updated": updated}


@router.get("/sites/{site_id}/hydraulic-config")
def get_hydraulic_config(
    site_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    cfg = db.query(SiteHydraulicConfig).filter(SiteHydraulicConfig.site_id == site_id).first()
    if not cfg:
        return {
            "site_id": site_id,
            "enabled": False,
            "pipe_shape": "circular",
            "depth_channel_id": None,
            "velocity_channel_id": None,
            "flow_channel_id": None,
            "diameter_m": None,
            "width_m": None,
            "height_m": None,
            "output_units": "L/s",
        }

    return {
        "site_id": site_id,
        "enabled": cfg.enabled,
        "pipe_shape": cfg.pipe_shape,
        "depth_channel_id": cfg.depth_channel_id,
        "velocity_channel_id": cfg.velocity_channel_id,
        "flow_channel_id": cfg.flow_channel_id,
        "diameter_m": cfg.diameter_m,
        "width_m": cfg.width_m,
        "height_m": cfg.height_m,
        "output_units": cfg.output_units,
    }


@router.post("/sites/{site_id}/hydraulic-config")
def upsert_hydraulic_config(
    site_id: int,
    payload: HydraulicConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    cfg = db.query(SiteHydraulicConfig).filter(SiteHydraulicConfig.site_id == site_id).first()
    if not cfg:
        cfg = SiteHydraulicConfig(site_id=site_id)
        db.add(cfg)

    cfg.enabled = payload.enabled
    cfg.pipe_shape = payload.pipe_shape
    cfg.depth_channel_id = payload.depth_channel_id
    cfg.velocity_channel_id = payload.velocity_channel_id
    cfg.flow_channel_id = payload.flow_channel_id
    cfg.diameter_m = payload.diameter_m
    cfg.width_m = payload.width_m
    cfg.height_m = payload.height_m
    cfg.output_units = payload.output_units

    db.commit()
    return {"site_id": site_id, "status": "saved"}


@router.post("/sites/{site_id}/hydraulic-config/create-flow-channel")
def create_flow_channel(
    site_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    device = db.query(Device).filter(Device.site_id == site_id).order_by(Device.device_id.asc()).first()
    if not device:
        raise HTTPException(status_code=404, detail="No device found for site")

    existing = (
        db.query(Channel)
        .filter(Channel.device_id == device.device_id, Channel.parameter == "flow_derived")
        .first()
    )
    if existing:
        return {"channel_id": existing.channel_id, "parameter": existing.parameter, "units": existing.units}

    channel = Channel(device_id=device.device_id, parameter="flow_derived", units="L/s")
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return {"channel_id": channel.channel_id, "parameter": channel.parameter, "units": channel.units}


@router.get("/logs")
def list_ingestion_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[dict]:
    logs = (
        db.query(IngestionJobLog)
        .order_by(IngestionJobLog.run_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": log.id,
            "run_at": log.run_at,
            "status": log.status,
            "message": log.message,
        }
        for log in logs
    ]
