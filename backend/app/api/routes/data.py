from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Channel, ChannelAdminSetting, Device, Site, TimeSeriesData, User
from app.db.session import get_db


router = APIRouter(prefix="/data", tags=["data"])


@router.get("/latest")
def latest(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    records = (
        db.query(TimeSeriesData, Channel, Device, Site, ChannelAdminSetting)
        .join(Channel, Channel.channel_id == TimeSeriesData.channel_id)
        .join(Device, Device.device_id == Channel.device_id)
        .join(Site, Site.site_id == Device.site_id)
        .outerjoin(
            ChannelAdminSetting,
            (ChannelAdminSetting.channel_id == Channel.channel_id) & (ChannelAdminSetting.site_id == Site.site_id),
        )
        .order_by(TimeSeriesData.timestamp.desc())
        .limit(1000)
        .all()
    )

    filtered = []
    for (t, c, d, s, setting) in records:
        if setting and not setting.is_viewable:
            continue
        filtered.append(
            {
                "site": s.site_name,
                "pmac": s.pmac_code,
                "device": d.device_name,
                "parameter": setting.display_name if setting and setting.display_name else c.parameter,
                "timestamp": t.timestamp,
                "value": t.value,
                "units": c.units,
                "channel_id": c.channel_id,
            }
        )

    return filtered[:400]


@router.get("/timeseries")
def timeseries(
    channel_id: int,
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    rows = (
        db.query(TimeSeriesData)
        .filter(
            TimeSeriesData.channel_id == channel_id,
            TimeSeriesData.timestamp >= start,
            TimeSeriesData.timestamp <= end,
        )
        .order_by(TimeSeriesData.timestamp.asc())
        .all()
    )
    return [{"timestamp": r.timestamp, "value": r.value} for r in rows]


@router.get("/export.csv")
def export_csv(
    channel_id: int,
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    rows = (
        db.query(TimeSeriesData)
        .filter(
            TimeSeriesData.channel_id == channel_id,
            TimeSeriesData.timestamp >= start,
            TimeSeriesData.timestamp <= end,
        )
        .order_by(TimeSeriesData.timestamp.asc())
        .all()
    )
    csv_lines = ["timestamp,value"]
    csv_lines.extend([f"{r.timestamp.isoformat()},{r.value}" for r in rows])
    csv_data = "\n".join(csv_lines)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=timeseries.csv"},
    )
