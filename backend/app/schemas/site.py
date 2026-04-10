from pydantic import BaseModel, Field


class SiteCreate(BaseModel):
    site_name: str
    pmac_code: str | None = Field(default=None, pattern=r"^\d{4}$")
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None


class SiteResponse(BaseModel):
    site_id: int
    site_name: str
    pmac_code: str | None
    latitude: float | None
    longitude: float | None
    description: str | None

    class Config:
        from_attributes = True
