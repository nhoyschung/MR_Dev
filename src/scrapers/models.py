"""Pydantic validation schemas for scraped data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ScrapedProjectData(BaseModel):
    """Validated data for a project scraped from BDS listing pages."""

    name: str = Field(min_length=1, max_length=300)
    slug: Optional[str] = None
    url: Optional[str] = None
    district_name: Optional[str] = None
    city_name: Optional[str] = None
    developer_name: Optional[str] = None
    total_units: Optional[int] = Field(default=None, ge=0)
    completion_date: Optional[str] = None
    price_range_raw: Optional[str] = None
    amenities: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class ScrapedListingData(BaseModel):
    """Validated data for an individual listing scraped from BDS."""

    bds_listing_id: Optional[str] = None
    project_name: Optional[str] = None
    district_name: Optional[str] = None
    city_name: Optional[str] = None
    price_raw: Optional[str] = None
    price_vnd: Optional[float] = Field(default=None, ge=0)
    price_per_sqm: Optional[float] = Field(default=None, ge=0)
    area_sqm: Optional[float] = Field(default=None, gt=0)
    bedrooms: Optional[int] = Field(default=None, ge=0, le=20)
    bathrooms: Optional[int] = Field(default=None, ge=0, le=20)
    floor: Optional[str] = None
    direction: Optional[str] = None
    listing_url: Optional[str] = None

    @field_validator("project_name")
    @classmethod
    def strip_project_name(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v

    @field_validator("direction")
    @classmethod
    def normalize_direction(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip().title()
        return v


class ScrapedOfficeListingData(BaseModel):
    """Validated data for an office lease listing scraped from BDS."""

    listing_id: Optional[str] = None
    building_name: Optional[str] = None
    address: Optional[str] = None
    district_name: Optional[str] = None
    city_name: Optional[str] = None
    rent_raw: Optional[str] = None
    rent_vnd_per_m2_month: Optional[float] = Field(default=None, ge=0)
    rent_usd_per_m2_month: Optional[float] = Field(default=None, ge=0)
    area_m2: Optional[float] = Field(default=None, gt=0)
    floor: Optional[str] = None
    listing_url: Optional[str] = None

    @field_validator("building_name", "district_name", "city_name", "address")
    @classmethod
    def strip_text(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class ScrapeJobResult(BaseModel):
    """Summary of a completed scrape job."""

    job_type: str
    target_url: Optional[str] = None
    status: str  # completed / failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items_found: int = 0
    items_saved: int = 0
    errors: list[str] = Field(default_factory=list)

    @property
    def duration_sec(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
