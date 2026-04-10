from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(str, Enum):
    admin = "admin"
    user = "user"


class Site(Base):
    __tablename__ = "sites"

    site_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    site_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    pmac_code: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    devices: Mapped[list["Device"]] = relationship("Device", back_populates="site", cascade="all, delete-orphan")
    permissions: Mapped[list["Permission"]] = relationship("Permission", back_populates="site", cascade="all, delete-orphan")
    hydraulic_config: Mapped["SiteHydraulicConfig | None"] = relationship(
        "SiteHydraulicConfig", back_populates="site", cascade="all, delete-orphan", uselist=False
    )


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=False)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    site: Mapped[Site] = relationship("Site", back_populates="devices")
    channels: Mapped[list["Channel"]] = relationship("Channel", back_populates="device", cascade="all, delete-orphan")
    polling_configs: Mapped[list["PollingConfig"]] = relationship("PollingConfig", back_populates="device")


class Channel(Base):
    __tablename__ = "channels"

    channel_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    parameter: Mapped[str] = mapped_column(String(50), nullable=False)
    units: Mapped[str | None] = mapped_column(String(50), nullable=True)

    device: Mapped[Device] = relationship("Device", back_populates="channels")
    timeseries: Mapped[list["TimeSeriesData"]] = relationship("TimeSeriesData", back_populates="channel", cascade="all, delete-orphan")
    admin_settings: Mapped[list["ChannelAdminSetting"]] = relationship("ChannelAdminSetting", back_populates="channel", cascade="all, delete-orphan")


class TimeSeriesData(Base):
    __tablename__ = "timeseries_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.channel_id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    channel: Mapped[Channel] = relationship("Channel", back_populates="timeseries")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SQLEnum(Role), default=Role.user, nullable=False)

    permissions: Mapped[list["Permission"]] = relationship("Permission", back_populates="user", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=False)
    channel_access: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="permissions")
    site: Mapped[Site] = relationship("Site", back_populates="permissions")


class PollingConfig(Base):
    __tablename__ = "polling_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=True)
    frequency_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    device: Mapped[Device | None] = relationship("Device", back_populates="polling_configs")


class IngestionJobLog(Base):
    __tablename__ = "ingestion_job_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    site_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ChannelAdminSetting(Base):
    __tablename__ = "channel_admin_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.channel_id", ondelete="CASCADE"), nullable=False, index=True)
    is_viewable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    channel: Mapped[Channel] = relationship("Channel", back_populates="admin_settings")


class SiteHydraulicConfig(Base):
    __tablename__ = "site_hydraulic_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pipe_shape: Mapped[str] = mapped_column(String(20), default="circular", nullable=False)
    depth_channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.channel_id", ondelete="SET NULL"), nullable=True)
    velocity_channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.channel_id", ondelete="SET NULL"), nullable=True)
    flow_channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.channel_id", ondelete="SET NULL"), nullable=True)
    diameter_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    output_units: Mapped[str] = mapped_column(String(20), default="L/s", nullable=False)

    site: Mapped[Site] = relationship("Site", back_populates="hydraulic_config")
