from datetime import datetime
import math

from sqlalchemy.orm import Session

from app.db.models import Channel, Device, IngestionJobLog, Site, SiteHydraulicConfig, TimeSeriesData
from app.services.detectdata_client import DetectDataClient


class IngestionService:
    def __init__(self) -> None:
        self.client = DetectDataClient()

    def _upsert_channel(
        self,
        db: Session,
        site_name: str,
        site_pmac: str | None,
        device_name: str,
        parameter: str,
        units: str | None,
    ) -> Channel:
        site = None
        if site_pmac:
            site = db.query(Site).filter(Site.pmac_code == site_pmac).first()
        if not site:
            site = db.query(Site).filter(Site.site_name == site_name).first()
        if not site:
            site = Site(site_name=site_name, pmac_code=site_pmac)
            db.add(site)
            db.flush()
        elif site_pmac and not site.pmac_code:
            site.pmac_code = site_pmac
            db.flush()

        device = (
            db.query(Device)
            .filter(Device.site_id == site.site_id, Device.device_name == device_name)
            .first()
        )
        if not device:
            device = Device(site_id=site.site_id, device_name=device_name, device_type="meter")
            db.add(device)
            db.flush()

        channel = (
            db.query(Channel)
            .filter(Channel.device_id == device.device_id, Channel.parameter == parameter)
            .first()
        )
        if not channel:
            channel = Channel(device_id=device.device_id, parameter=parameter, units=units)
            db.add(channel)
            db.flush()

        return channel

    def _insert_readings(self, db: Session, readings) -> tuple[int, int]:
        inserted = 0
        skipped = 0

        for reading in readings:
            channel = self._upsert_channel(
                db,
                site_name=reading.site_name,
                site_pmac=reading.site_pmac,
                device_name=reading.device_name,
                parameter=reading.channel_parameter,
                units=reading.units,
            )

            existing = (
                db.query(TimeSeriesData.id)
                .filter(TimeSeriesData.channel_id == channel.channel_id, TimeSeriesData.timestamp == reading.timestamp)
                .first()
            )
            if existing:
                skipped += 1
                continue

            db.add(
                TimeSeriesData(
                    channel_id=channel.channel_id,
                    timestamp=reading.timestamp or datetime.utcnow(),
                    value=reading.value,
                )
            )
            inserted += 1

        return inserted, skipped

    @staticmethod
    def _compute_area(shape: str, depth: float, diameter_m: float | None, width_m: float | None, height_m: float | None) -> float | None:
        if depth <= 0:
            return 0.0

        if shape == "circular":
            if not diameter_m or diameter_m <= 0:
                return None
            d = diameter_m
            h = max(0.0, min(depth, d))
            if h == 0:
                return 0.0
            if h >= d:
                return math.pi * (d / 2.0) ** 2
            r = d / 2.0
            theta = 2.0 * math.acos((r - h) / r)
            return 0.5 * r * r * (theta - math.sin(theta))

        if shape == "square":
            if not width_m or width_m <= 0:
                return None
            effective_h = depth
            if height_m and height_m > 0:
                effective_h = min(depth, height_m)
            return width_m * max(effective_h, 0.0)

        return None

    def _apply_derived_flow(self, db: Session) -> int:
        inserted = 0
        configs = db.query(SiteHydraulicConfig).filter(SiteHydraulicConfig.enabled.is_(True)).all()
        for cfg in configs:
            if not cfg.depth_channel_id or not cfg.velocity_channel_id or not cfg.flow_channel_id:
                continue

            depth_row = (
                db.query(TimeSeriesData)
                .filter(TimeSeriesData.channel_id == cfg.depth_channel_id)
                .order_by(TimeSeriesData.timestamp.desc())
                .first()
            )
            velocity_row = (
                db.query(TimeSeriesData)
                .filter(TimeSeriesData.channel_id == cfg.velocity_channel_id)
                .order_by(TimeSeriesData.timestamp.desc())
                .first()
            )
            if not depth_row or not velocity_row:
                continue

            area = self._compute_area(
                shape=cfg.pipe_shape,
                depth=depth_row.value,
                diameter_m=cfg.diameter_m,
                width_m=cfg.width_m,
                height_m=cfg.height_m,
            )
            if area is None:
                continue

            flow_m3s = area * velocity_row.value
            flow_value = flow_m3s * 1000.0 if cfg.output_units.lower() in {"l/s", "ls", "lps"} else flow_m3s
            flow_ts = max(depth_row.timestamp, velocity_row.timestamp)

            exists = (
                db.query(TimeSeriesData.id)
                .filter(TimeSeriesData.channel_id == cfg.flow_channel_id, TimeSeriesData.timestamp == flow_ts)
                .first()
            )
            if exists:
                continue

            db.add(TimeSeriesData(channel_id=cfg.flow_channel_id, timestamp=flow_ts, value=flow_value))
            inserted += 1

        return inserted

    def sync_all(self, db: Session) -> dict:
        channel_defs, readings = self.client.fetch_all(days_back=3)

        for channel_def in channel_defs:
            self._upsert_channel(
                db,
                site_name=channel_def.site_name,
                site_pmac=channel_def.site_pmac,
                device_name=channel_def.device_name,
                parameter=channel_def.channel_parameter,
                units=channel_def.units,
            )

        inserted, skipped = self._insert_readings(db, readings)
        derived_inserted = self._apply_derived_flow(db)

        status = "success"
        message = f"Inserted {inserted} records, skipped {skipped} duplicates, derived {derived_inserted} flow records"
        db.add(IngestionJobLog(status=status, message=message))
        db.commit()
        return {
            "status": status,
            "inserted": inserted,
            "skipped": skipped,
            "derived_inserted": derived_inserted,
            "sites": len({c.site_pmac for c in channel_defs}),
        }

    def backfill_all(self, db: Session, days_back: int = 3650, chunk_days: int = 90) -> dict:
        inventory = self.client.fetch_inventory()
        for channel_def in inventory:
            self._upsert_channel(
                db,
                site_name=channel_def.site_name,
                site_pmac=channel_def.site_pmac,
                device_name=channel_def.device_name,
                parameter=channel_def.channel_parameter,
                units=channel_def.units,
            )

        readings = self.client.fetch_readings(
            channel_defs=inventory,
            days_back=max(days_back, 1),
            latest_only=False,
            chunk_days=max(chunk_days, 1),
        )
        inserted, skipped = self._insert_readings(db, readings)
        derived_inserted = self._apply_derived_flow(db)

        status = "success"
        message = f"Backfill inserted {inserted} records, skipped {skipped} duplicates, derived {derived_inserted} flow records"
        db.add(IngestionJobLog(status=status, message=message))
        db.commit()
        return {
            "status": status,
            "inserted": inserted,
            "skipped": skipped,
            "derived_inserted": derived_inserted,
            "sites": len({c.site_pmac for c in inventory}),
            "days_back": days_back,
            "chunk_days": chunk_days,
        }
