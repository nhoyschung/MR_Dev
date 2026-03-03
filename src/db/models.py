"""SQLAlchemy 2.x declarative models for the MR-System database."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Float, Integer, DateTime, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Reference Tables
# ---------------------------------------------------------------------------

class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_en: Mapped[str] = mapped_column(String(100), unique=True)
    name_vi: Mapped[Optional[str]] = mapped_column(String(100))
    name_ko: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[str] = mapped_column(String(20))  # South / North / Central

    districts: Mapped[list[District]] = relationship(back_populates="city")
    grade_definitions: Mapped[list[GradeDefinition]] = relationship(back_populates="city")
    developers: Mapped[list[Developer]] = relationship(back_populates="hq_city")
    source_reports: Mapped[list[SourceReport]] = relationship(back_populates="city")
    market_segment_summaries: Mapped[list[MarketSegmentSummary]] = relationship(back_populates="city")
    office_projects: Mapped[list["OfficeProject"]] = relationship(back_populates="city")
    hotel_projects: Mapped[list["HotelProject"]] = relationship(back_populates="city")
    office_market_summaries: Mapped[list["OfficeMarketSummary"]] = relationship(back_populates="city")
    hotel_performance_records: Mapped[list["HotelPerformanceRecord"]] = relationship(
        foreign_keys="HotelPerformanceRecord.city_id", back_populates="city"
    )

    def __repr__(self) -> str:
        return f"<City {self.name_en}>"


class District(Base):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    name_en: Mapped[str] = mapped_column(String(100))
    name_vi: Mapped[Optional[str]] = mapped_column(String(100))
    name_ko: Mapped[Optional[str]] = mapped_column(String(100))
    district_type: Mapped[Optional[str]] = mapped_column(String(20))  # urban / suburban

    city: Mapped[City] = relationship(back_populates="districts")
    wards: Mapped[list[Ward]] = relationship(back_populates="district")
    projects: Mapped[list[Project]] = relationship(back_populates="district")
    supply_records: Mapped[list[SupplyRecord]] = relationship(back_populates="district")
    district_metrics: Mapped[list[DistrictMetric]] = relationship(back_populates="district")
    market_segment_summaries: Mapped[list[MarketSegmentSummary]] = relationship(back_populates="district")
    office_projects: Mapped[list["OfficeProject"]] = relationship(back_populates="district")
    hotel_projects: Mapped[list["HotelProject"]] = relationship(back_populates="district")
    office_market_summaries: Mapped[list["OfficeMarketSummary"]] = relationship(back_populates="district")
    hotel_performance_records: Mapped[list["HotelPerformanceRecord"]] = relationship(
        foreign_keys="HotelPerformanceRecord.district_id", back_populates="district"
    )

    def __repr__(self) -> str:
        return f"<District {self.name_en}>"


class Ward(Base):
    __tablename__ = "wards"

    id: Mapped[int] = mapped_column(primary_key=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"))
    name_en: Mapped[str] = mapped_column(String(100))
    name_vi: Mapped[Optional[str]] = mapped_column(String(100))

    district: Mapped[District] = relationship(back_populates="wards")
    projects: Mapped[list[Project]] = relationship(back_populates="ward")

    def __repr__(self) -> str:
        return f"<Ward {self.name_en}>"


# ---------------------------------------------------------------------------
# Grade System
# ---------------------------------------------------------------------------

class ReportPeriod(Base):
    __tablename__ = "report_periods"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer)
    half: Mapped[str] = mapped_column(String(2))  # H1 / H2
    report_date: Mapped[Optional[date]] = mapped_column(Date)
    report_type: Mapped[Optional[str]] = mapped_column(String(50))

    grade_definitions: Mapped[list[GradeDefinition]] = relationship(back_populates="period")
    price_records: Mapped[list[PriceRecord]] = relationship(back_populates="period")
    supply_records: Mapped[list[SupplyRecord]] = relationship(back_populates="period")
    sales_statuses: Mapped[list[SalesStatus]] = relationship(back_populates="period")
    competitor_comparisons: Mapped[list[CompetitorComparison]] = relationship(back_populates="period")
    market_segment_summaries: Mapped[list[MarketSegmentSummary]] = relationship(back_populates="period")
    source_reports: Mapped[list[SourceReport]] = relationship(back_populates="period")
    district_metrics: Mapped[list[DistrictMetric]] = relationship(back_populates="period")
    macro_indicators: Mapped[list["MacroIndicator"]] = relationship(back_populates="period")
    office_leasing_records: Mapped[list["OfficeLeasingRecord"]] = relationship(back_populates="period")
    office_market_summaries: Mapped[list["OfficeMarketSummary"]] = relationship(back_populates="period")
    hotel_performance_records: Mapped[list["HotelPerformanceRecord"]] = relationship(back_populates="period")

    def __repr__(self) -> str:
        return f"<ReportPeriod {self.year}-{self.half}>"


class GradeDefinition(Base):
    __tablename__ = "grade_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    grade_code: Mapped[str] = mapped_column(String(10))  # SL, L, H-I, H-II, M-I, M-II, M-III, A-I, A-II
    min_price_usd: Mapped[Optional[float]] = mapped_column(Float)
    max_price_usd: Mapped[Optional[float]] = mapped_column(Float)
    segment: Mapped[str] = mapped_column(String(30))  # super-luxury / luxury / high-end / mid-end / affordable
    period_id: Mapped[Optional[int]] = mapped_column(ForeignKey("report_periods.id"))

    city: Mapped[City] = relationship(back_populates="grade_definitions")
    period: Mapped[Optional[ReportPeriod]] = relationship(back_populates="grade_definitions")

    def __repr__(self) -> str:
        return f"<GradeDefinition {self.grade_code} ({self.segment})>"


# ---------------------------------------------------------------------------
# Core Market Intelligence
# ---------------------------------------------------------------------------

class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_en: Mapped[str] = mapped_column(String(200), unique=True)
    name_vi: Mapped[Optional[str]] = mapped_column(String(200))
    stock_code: Mapped[Optional[str]] = mapped_column(String(20))
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    hq_city_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cities.id"))
    established_year: Mapped[Optional[int]] = mapped_column(Integer)
    website: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)

    hq_city: Mapped[Optional[City]] = relationship(back_populates="developers")
    projects: Mapped[list[Project]] = relationship(back_populates="developer")

    def __repr__(self) -> str:
        return f"<Developer {self.name_en}>"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    developer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("developers.id"))
    district_id: Mapped[Optional[int]] = mapped_column(ForeignKey("districts.id"))
    ward_id: Mapped[Optional[int]] = mapped_column(ForeignKey("wards.id"))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    total_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    total_units: Mapped[Optional[int]] = mapped_column(Integer)
    project_type: Mapped[Optional[str]] = mapped_column(String(30))
    status: Mapped[Optional[str]] = mapped_column(String(30))
    launch_date: Mapped[Optional[str]] = mapped_column(String(20))
    completion_date: Mapped[Optional[str]] = mapped_column(String(20))
    grade_primary: Mapped[Optional[str]] = mapped_column(String(10))
    grade_secondary: Mapped[Optional[str]] = mapped_column(String(10))
    bds_slug: Mapped[Optional[str]] = mapped_column(String(200))
    bds_url: Mapped[Optional[str]] = mapped_column(String(500))

    developer: Mapped[Optional[Developer]] = relationship(back_populates="projects")
    district: Mapped[Optional[District]] = relationship(back_populates="projects")
    ward: Mapped[Optional[Ward]] = relationship(back_populates="projects")
    blocks: Mapped[list[ProjectBlock]] = relationship(back_populates="project")
    unit_types: Mapped[list[UnitType]] = relationship(back_populates="project")
    price_records: Mapped[list[PriceRecord]] = relationship(back_populates="project")
    supply_records: Mapped[list[SupplyRecord]] = relationship(back_populates="project")
    sales_statuses: Mapped[list[SalesStatus]] = relationship(back_populates="project")
    facilities: Mapped[list[ProjectFacility]] = relationship(back_populates="project")
    sales_points: Mapped[list[ProjectSalesPoint]] = relationship(back_populates="project")
    subject_comparisons: Mapped[list[CompetitorComparison]] = relationship(
        foreign_keys="CompetitorComparison.subject_project_id", back_populates="subject_project"
    )
    competitor_comparisons: Mapped[list[CompetitorComparison]] = relationship(
        foreign_keys="CompetitorComparison.competitor_project_id", back_populates="competitor_project"
    )
    scraped_listings: Mapped[list[ScrapedListing]] = relationship(back_populates="matched_project")

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class ProjectBlock(Base):
    __tablename__ = "project_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    block_name: Mapped[str] = mapped_column(String(50))
    floors: Mapped[Optional[int]] = mapped_column(Integer)
    units_per_floor: Mapped[Optional[int]] = mapped_column(Integer)
    total_units: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(30))

    project: Mapped[Project] = relationship(back_populates="blocks")
    unit_types: Mapped[list[UnitType]] = relationship(back_populates="block")
    sales_statuses: Mapped[list[SalesStatus]] = relationship(back_populates="block")

    def __repr__(self) -> str:
        return f"<ProjectBlock {self.block_name}>"


class UnitType(Base):
    __tablename__ = "unit_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    block_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_blocks.id"))
    type_name: Mapped[str] = mapped_column(String(30))
    net_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    gross_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    unit_count: Mapped[Optional[int]] = mapped_column(Integer)
    typical_layout_description: Mapped[Optional[str]] = mapped_column(Text)

    project: Mapped[Project] = relationship(back_populates="unit_types")
    block: Mapped[Optional[ProjectBlock]] = relationship(back_populates="unit_types")
    price_records: Mapped[list[PriceRecord]] = relationship(back_populates="unit_type")

    def __repr__(self) -> str:
        return f"<UnitType {self.type_name}>"


class PriceRecord(Base):
    __tablename__ = "price_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    unit_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("unit_types.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    price_vnd_per_m2: Mapped[Optional[float]] = mapped_column(Float)
    price_usd_per_m2: Mapped[Optional[float]] = mapped_column(Float)
    price_change_pct: Mapped[Optional[float]] = mapped_column(Float)
    price_incl_vat: Mapped[Optional[bool]] = mapped_column(default=True)
    source_report: Mapped[Optional[str]] = mapped_column(String(200))
    data_source: Mapped[Optional[str]] = mapped_column(String(20), default="nho_pdf")
    # data_source: 'nho_pdf' | 'bds_scrape' | 'manual'

    project: Mapped[Project] = relationship(back_populates="price_records")
    unit_type: Mapped[Optional[UnitType]] = relationship(back_populates="price_records")
    period: Mapped[ReportPeriod] = relationship(back_populates="price_records")
    change_factors: Mapped[list[PriceChangeFactor]] = relationship(back_populates="price_record")

    def __repr__(self) -> str:
        return f"<PriceRecord project={self.project_id} ${self.price_usd_per_m2}/m2>"


class PriceChangeFactor(Base):
    __tablename__ = "price_change_factors"

    id: Mapped[int] = mapped_column(primary_key=True)
    price_record_id: Mapped[int] = mapped_column(ForeignKey("price_records.id"))
    factor_type: Mapped[str] = mapped_column(String(20))  # increase / decrease
    factor_category: Mapped[str] = mapped_column(String(30))
    description: Mapped[Optional[str]] = mapped_column(Text)

    price_record: Mapped[PriceRecord] = relationship(back_populates="change_factors")

    def __repr__(self) -> str:
        return f"<PriceChangeFactor {self.factor_type}: {self.factor_category}>"


# ---------------------------------------------------------------------------
# Supply & Sales
# ---------------------------------------------------------------------------

class SupplyRecord(Base):
    __tablename__ = "supply_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    district_id: Mapped[Optional[int]] = mapped_column(ForeignKey("districts.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    total_inventory: Mapped[Optional[int]] = mapped_column(Integer)
    new_supply: Mapped[Optional[int]] = mapped_column(Integer)
    sold_units: Mapped[Optional[int]] = mapped_column(Integer)
    absorption_rate_pct: Mapped[Optional[float]] = mapped_column(Float)
    remaining_inventory: Mapped[Optional[int]] = mapped_column(Integer)

    project: Mapped[Optional[Project]] = relationship(back_populates="supply_records")
    district: Mapped[Optional[District]] = relationship(back_populates="supply_records")
    period: Mapped[ReportPeriod] = relationship(back_populates="supply_records")

    def __repr__(self) -> str:
        return f"<SupplyRecord inventory={self.total_inventory}>"


class SalesStatus(Base):
    __tablename__ = "sales_statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    block_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_blocks.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    launched_units: Mapped[Optional[int]] = mapped_column(Integer)
    sold_units: Mapped[Optional[int]] = mapped_column(Integer)
    held_units: Mapped[Optional[int]] = mapped_column(Integer)
    available_units: Mapped[Optional[int]] = mapped_column(Integer)
    sales_rate_pct: Mapped[Optional[float]] = mapped_column(Float)

    project: Mapped[Project] = relationship(back_populates="sales_statuses")
    block: Mapped[Optional[ProjectBlock]] = relationship(back_populates="sales_statuses")
    period: Mapped[ReportPeriod] = relationship(back_populates="sales_statuses")

    def __repr__(self) -> str:
        return f"<SalesStatus sold={self.sold_units}/{self.launched_units}>"


# ---------------------------------------------------------------------------
# Facilities & Features
# ---------------------------------------------------------------------------

class ProjectFacility(Base):
    __tablename__ = "project_facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    facility_type: Mapped[str] = mapped_column(String(30))
    facility_name: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)

    project: Mapped[Project] = relationship(back_populates="facilities")

    def __repr__(self) -> str:
        return f"<ProjectFacility {self.facility_type}>"


class ProjectSalesPoint(Base):
    __tablename__ = "project_sales_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    category: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text)
    ranking: Mapped[Optional[int]] = mapped_column(Integer)

    project: Mapped[Project] = relationship(back_populates="sales_points")

    def __repr__(self) -> str:
        return f"<ProjectSalesPoint {self.category}>"


# ---------------------------------------------------------------------------
# Competitive Analysis
# ---------------------------------------------------------------------------

class CompetitorComparison(Base):
    __tablename__ = "competitor_comparisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    competitor_project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    dimension: Mapped[str] = mapped_column(String(30))
    subject_score: Mapped[Optional[float]] = mapped_column(Float)
    competitor_score: Mapped[Optional[float]] = mapped_column(Float)
    analysis_notes: Mapped[Optional[str]] = mapped_column(Text)

    subject_project: Mapped[Project] = relationship(
        foreign_keys=[subject_project_id], back_populates="subject_comparisons"
    )
    competitor_project: Mapped[Project] = relationship(
        foreign_keys=[competitor_project_id], back_populates="competitor_comparisons"
    )
    period: Mapped[ReportPeriod] = relationship(back_populates="competitor_comparisons")

    def __repr__(self) -> str:
        return f"<CompetitorComparison {self.dimension}>"


class MarketSegmentSummary(Base):
    __tablename__ = "market_segment_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    district_id: Mapped[Optional[int]] = mapped_column(ForeignKey("districts.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    grade_code: Mapped[Optional[str]] = mapped_column(String(10))
    segment: Mapped[Optional[str]] = mapped_column(String(30))
    avg_price_usd: Mapped[Optional[float]] = mapped_column(Float)
    total_supply: Mapped[Optional[int]] = mapped_column(Integer)
    total_sold: Mapped[Optional[int]] = mapped_column(Integer)
    absorption_rate: Mapped[Optional[float]] = mapped_column(Float)
    new_launches: Mapped[Optional[int]] = mapped_column(Integer)

    city: Mapped[City] = relationship(back_populates="market_segment_summaries")
    district: Mapped[Optional[District]] = relationship(back_populates="market_segment_summaries")
    period: Mapped[ReportPeriod] = relationship(back_populates="market_segment_summaries")

    def __repr__(self) -> str:
        return f"<MarketSegmentSummary {self.segment} {self.grade_code}>"


# ---------------------------------------------------------------------------
# Report Tracking
# ---------------------------------------------------------------------------

class SourceReport(Base):
    __tablename__ = "source_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(300))
    report_type: Mapped[str] = mapped_column(String(50))
    city_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cities.id"))
    period_id: Mapped[Optional[int]] = mapped_column(ForeignKey("report_periods.id"))
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    ingested_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    status: Mapped[Optional[str]] = mapped_column(String(30), default="pending")

    # PDF metadata fields (added for collection system)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size_mb: Mapped[Optional[float]] = mapped_column(Float)
    pdf_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Extraction tracking fields
    extraction_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    extraction_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    extraction_time_sec: Mapped[Optional[float]] = mapped_column(Float)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    extracted_text_length: Mapped[Optional[int]] = mapped_column(Integer)

    city: Mapped[Optional[City]] = relationship(back_populates="source_reports")
    period: Mapped[Optional[ReportPeriod]] = relationship(back_populates="source_reports")
    data_lineage_records: Mapped[list[DataLineage]] = relationship(back_populates="source_report")

    def __repr__(self) -> str:
        return f"<SourceReport {self.filename}>"


class DataLineage(Base):
    __tablename__ = "data_lineage"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_name: Mapped[str] = mapped_column(String(100))
    record_id: Mapped[int] = mapped_column(Integer)
    source_report_id: Mapped[int] = mapped_column(ForeignKey("source_reports.id"))
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    source_report: Mapped[SourceReport] = relationship(back_populates="data_lineage_records")

    def __repr__(self) -> str:
        return f"<DataLineage {self.table_name}:{self.record_id}>"


# ---------------------------------------------------------------------------
# Market Metrics
# ---------------------------------------------------------------------------

class DistrictMetric(Base):
    __tablename__ = "district_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    metric_type: Mapped[str] = mapped_column(String(30))
    value_numeric: Mapped[Optional[float]] = mapped_column(Float)
    value_text: Mapped[Optional[str]] = mapped_column(Text)

    district: Mapped[District] = relationship(back_populates="district_metrics")
    period: Mapped[ReportPeriod] = relationship(back_populates="district_metrics")

    def __repr__(self) -> str:
        return f"<DistrictMetric {self.metric_type}={self.value_numeric}>"


# ---------------------------------------------------------------------------
# Macro Indicators
# ---------------------------------------------------------------------------

class MacroIndicator(Base):
    """National or city-level macroeconomic indicators by half-year period.

    indicator_type values:
        gdp_growth_pct      – Real GDP growth rate (%)
        cpi_pct             – Consumer price inflation (%)
        mortgage_rate_pct   – Average housing mortgage rate (%)
        policy_rate_pct     – State Bank of Vietnam policy rate (%)
        fdi_usd_billion     – Foreign direct investment (USD billion)
        housing_starts      – New housing units started (units)
        exchange_rate_vnd   – USD/VND exchange rate (VND per 1 USD)
    """
    __tablename__ = "macro_indicators"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    indicator_type: Mapped[str] = mapped_column(String(40))
    value: Mapped[float] = mapped_column(Float)
    city_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cities.id"))
    source: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    period: Mapped[ReportPeriod] = relationship(back_populates="macro_indicators")
    city: Mapped[Optional[City]] = relationship()

    def __repr__(self) -> str:
        return f"<MacroIndicator {self.indicator_type}={self.value} ({self.period_id})>"


# ---------------------------------------------------------------------------
# Web Scraping
# ---------------------------------------------------------------------------

class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(50))  # project_list / project_detail / listing
    target_url: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/running/completed/failed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    items_found: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    items_saved: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    listings: Mapped[list[ScrapedListing]] = relationship(back_populates="scrape_job")

    def __repr__(self) -> str:
        return f"<ScrapeJob {self.job_type} {self.status}>"


class ScrapedListing(Base):
    __tablename__ = "scraped_listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_job_id: Mapped[int] = mapped_column(ForeignKey("scrape_jobs.id"))
    bds_listing_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    project_name: Mapped[Optional[str]] = mapped_column(String(300))
    district_name: Mapped[Optional[str]] = mapped_column(String(100))
    city_name: Mapped[Optional[str]] = mapped_column(String(100))
    price_raw: Mapped[Optional[str]] = mapped_column(String(100))
    price_vnd: Mapped[Optional[float]] = mapped_column(Float)
    price_per_sqm: Mapped[Optional[float]] = mapped_column(Float)
    area_sqm: Mapped[Optional[float]] = mapped_column(Float)
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[int]] = mapped_column(Integer)
    floor: Mapped[Optional[str]] = mapped_column(String(20))
    direction: Mapped[Optional[str]] = mapped_column(String(30))
    listing_url: Mapped[Optional[str]] = mapped_column(String(500))
    scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    matched_project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    promoted: Mapped[bool] = mapped_column(default=False)
    reconcile_status: Mapped[Optional[str]] = mapped_column(String(30))
    reconcile_detail: Mapped[Optional[str]] = mapped_column(Text)

    scrape_job: Mapped[ScrapeJob] = relationship(back_populates="listings")
    matched_project: Mapped[Optional[Project]] = relationship(back_populates="scraped_listings")

    def __repr__(self) -> str:
        return f"<ScrapedListing {self.bds_listing_id} {self.project_name}>"


class ScrapedOfficeListing(Base):
    """Staging table for office lease listings scraped from web sources.

    rent fields are per m² per month (the industry standard for Vietnam office).
    If the source provides total monthly rent, compute per-m² using area_m2.
    Promoted records are written to office_leasing_records.
    """
    __tablename__ = "scraped_office_listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_job_id: Mapped[int] = mapped_column(ForeignKey("scrape_jobs.id"))
    listing_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    building_name: Mapped[Optional[str]] = mapped_column(String(300))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    district_name: Mapped[Optional[str]] = mapped_column(String(100))
    city_name: Mapped[Optional[str]] = mapped_column(String(100))
    rent_raw: Mapped[Optional[str]] = mapped_column(String(200))
    rent_vnd_per_m2_month: Mapped[Optional[float]] = mapped_column(Float)
    rent_usd_per_m2_month: Mapped[Optional[float]] = mapped_column(Float)
    area_m2: Mapped[Optional[float]] = mapped_column(Float)
    floor: Mapped[Optional[str]] = mapped_column(String(30))
    listing_url: Mapped[Optional[str]] = mapped_column(String(500))
    scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    matched_office_project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("office_projects.id")
    )
    promoted: Mapped[bool] = mapped_column(default=False)
    reconcile_status: Mapped[Optional[str]] = mapped_column(String(30))
    reconcile_detail: Mapped[Optional[str]] = mapped_column(Text)

    scrape_job: Mapped[ScrapeJob] = relationship()
    matched_office_project: Mapped[Optional["OfficeProject"]] = relationship()

    def __repr__(self) -> str:
        return f"<ScrapedOfficeListing {self.listing_id} {self.building_name}>"


# ---------------------------------------------------------------------------
# Office Market
# ---------------------------------------------------------------------------

class OfficeProject(Base):
    """Individual office building profile.

    office_grade values: A / B+ / B / C
    area_calculation_basis values: NLA / GLA
    green_certificate examples: 'LEED Platinum', 'LEED Gold', 'DGNB Gold', 'Green Mark'
    """
    __tablename__ = "office_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    developer_name: Mapped[Optional[str]] = mapped_column(String(200))
    investor_name: Mapped[Optional[str]] = mapped_column(String(200))
    management_company: Mapped[Optional[str]] = mapped_column(String(200))
    city_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cities.id"))
    district_id: Mapped[Optional[int]] = mapped_column(ForeignKey("districts.id"))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    office_grade: Mapped[Optional[str]] = mapped_column(String(5))   # A / B+ / B / C
    operation_year: Mapped[Optional[int]] = mapped_column(Integer)
    operation_quarter: Mapped[Optional[str]] = mapped_column(String(2))  # Q1–Q4
    total_floors: Mapped[Optional[int]] = mapped_column(Integer)
    num_office_floors: Mapped[Optional[int]] = mapped_column(Integer)
    num_basements: Mapped[Optional[int]] = mapped_column(Integer)
    total_leasing_area_m2: Mapped[Optional[float]] = mapped_column(Float)   # NLA
    total_gfa_m2: Mapped[Optional[float]] = mapped_column(Float)            # GLA if known
    avg_floor_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    ceiling_height_m: Mapped[Optional[float]] = mapped_column(Float)
    raised_floor_cm: Mapped[Optional[int]] = mapped_column(Integer)
    lift_passenger: Mapped[Optional[int]] = mapped_column(Integer)
    lift_service: Mapped[Optional[int]] = mapped_column(Integer)
    green_certificate: Mapped[Optional[str]] = mapped_column(String(100))
    area_calculation_basis: Mapped[Optional[str]] = mapped_column(String(5))  # NLA / GLA
    has_conference: Mapped[Optional[bool]] = mapped_column(default=False)
    has_sky_terrace: Mapped[Optional[bool]] = mapped_column(default=False)
    has_gym: Mapped[Optional[bool]] = mapped_column(default=False)
    has_coworking: Mapped[Optional[bool]] = mapped_column(default=False)
    has_retail: Mapped[Optional[bool]] = mapped_column(default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    source_report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("source_reports.id"))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    city: Mapped[Optional[City]] = relationship(back_populates="office_projects")
    district: Mapped[Optional[District]] = relationship(back_populates="office_projects")
    source_report: Mapped[Optional[SourceReport]] = relationship()
    leasing_records: Mapped[list["OfficeLeasingRecord"]] = relationship(back_populates="office_project")

    def __repr__(self) -> str:
        return f"<OfficeProject {self.name} Grade-{self.office_grade}>"


class OfficeLeasingRecord(Base):
    """Rental data for an office building in a given half-year period.

    rent fields are USD/m²/month (standard Vietnam office quoting convention).
    """
    __tablename__ = "office_leasing_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    office_project_id: Mapped[int] = mapped_column(ForeignKey("office_projects.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    rent_min_usd: Mapped[Optional[float]] = mapped_column(Float)   # $/m²/month
    rent_max_usd: Mapped[Optional[float]] = mapped_column(Float)
    management_fee_usd: Mapped[Optional[float]] = mapped_column(Float)
    occupancy_rate_pct: Mapped[Optional[float]] = mapped_column(Float)
    area_basis: Mapped[Optional[str]] = mapped_column(String(5))   # NLA / GLA
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    office_project: Mapped[OfficeProject] = relationship(back_populates="leasing_records")
    period: Mapped[ReportPeriod] = relationship(back_populates="office_leasing_records")

    def __repr__(self) -> str:
        return f"<OfficeLeasingRecord project={self.office_project_id} ${self.rent_min_usd}-{self.rent_max_usd}/m²/mo>"


class OfficeMarketSummary(Base):
    """City/district-level office market statistics per half-year period."""
    __tablename__ = "office_market_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    district_id: Mapped[Optional[int]] = mapped_column(ForeignKey("districts.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    total_stock_nla_m2: Mapped[Optional[float]] = mapped_column(Float)
    grade_a_stock_m2: Mapped[Optional[float]] = mapped_column(Float)
    grade_b_stock_m2: Mapped[Optional[float]] = mapped_column(Float)
    grade_c_stock_m2: Mapped[Optional[float]] = mapped_column(Float)
    num_projects_total: Mapped[Optional[int]] = mapped_column(Integer)
    num_projects_grade_a: Mapped[Optional[int]] = mapped_column(Integer)
    avg_rent_usd_grade_a: Mapped[Optional[float]] = mapped_column(Float)
    avg_rent_usd_grade_b: Mapped[Optional[float]] = mapped_column(Float)
    avg_rent_usd_grade_c: Mapped[Optional[float]] = mapped_column(Float)
    avg_occupancy_grade_a_pct: Mapped[Optional[float]] = mapped_column(Float)
    avg_occupancy_grade_b_pct: Mapped[Optional[float]] = mapped_column(Float)
    avg_occupancy_grade_c_pct: Mapped[Optional[float]] = mapped_column(Float)
    net_absorption_m2: Mapped[Optional[float]] = mapped_column(Float)
    new_supply_m2: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    city: Mapped[City] = relationship(back_populates="office_market_summaries")
    district: Mapped[Optional[District]] = relationship(back_populates="office_market_summaries")
    period: Mapped[ReportPeriod] = relationship(back_populates="office_market_summaries")

    def __repr__(self) -> str:
        return f"<OfficeMarketSummary city={self.city_id} {self.total_stock_nla_m2}m² NLA>"


# ---------------------------------------------------------------------------
# Hotel Market
# ---------------------------------------------------------------------------

class HotelProject(Base):
    """Individual hotel property profile.

    star_rating: 1–5
    hotel_type: boutique / business / resort / serviced_apartment / mixed_use
    """
    __tablename__ = "hotel_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[Optional[str]] = mapped_column(String(100))        # e.g. 'M Village', 'Sheraton'
    operator: Mapped[Optional[str]] = mapped_column(String(200))
    investor_name: Mapped[Optional[str]] = mapped_column(String(200))
    developer_name: Mapped[Optional[str]] = mapped_column(String(200))
    city_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cities.id"))
    district_id: Mapped[Optional[int]] = mapped_column(ForeignKey("districts.id"))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    star_rating: Mapped[Optional[int]] = mapped_column(Integer)
    hotel_type: Mapped[Optional[str]] = mapped_column(String(30))
    total_rooms: Mapped[Optional[int]] = mapped_column(Integer)
    operation_year: Mapped[Optional[int]] = mapped_column(Integer)
    operation_quarter: Mapped[Optional[str]] = mapped_column(String(2))
    total_floors: Mapped[Optional[int]] = mapped_column(Integer)
    num_basements: Mapped[Optional[int]] = mapped_column(Integer)
    land_area_m2: Mapped[Optional[float]] = mapped_column(Float)
    total_gfa_m2: Mapped[Optional[float]] = mapped_column(Float)
    has_pool: Mapped[Optional[bool]] = mapped_column(default=False)
    has_gym: Mapped[Optional[bool]] = mapped_column(default=False)
    has_spa: Mapped[Optional[bool]] = mapped_column(default=False)
    has_restaurant: Mapped[Optional[bool]] = mapped_column(default=False)
    has_ballroom: Mapped[Optional[bool]] = mapped_column(default=False)
    has_sky_bar: Mapped[Optional[bool]] = mapped_column(default=False)
    has_conference: Mapped[Optional[bool]] = mapped_column(default=False)
    has_coworking: Mapped[Optional[bool]] = mapped_column(default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    source_report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("source_reports.id"))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    city: Mapped[Optional[City]] = relationship(back_populates="hotel_projects")
    district: Mapped[Optional[District]] = relationship(back_populates="hotel_projects")
    source_report: Mapped[Optional[SourceReport]] = relationship()
    room_types: Mapped[list["HotelRoomType"]] = relationship(back_populates="hotel_project")
    performance_records: Mapped[list["HotelPerformanceRecord"]] = relationship(
        foreign_keys="HotelPerformanceRecord.hotel_project_id", back_populates="hotel_project"
    )

    def __repr__(self) -> str:
        return f"<HotelProject {self.name} {self.star_rating}★ {self.total_rooms}rooms>"


class HotelRoomType(Base):
    """Room type breakdown for a hotel property.

    room_type values: standard / deluxe / family_deluxe / executive / suite / penthouse
    """
    __tablename__ = "hotel_room_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    hotel_project_id: Mapped[int] = mapped_column(ForeignKey("hotel_projects.id"))
    room_type: Mapped[str] = mapped_column(String(30))
    area_m2: Mapped[Optional[float]] = mapped_column(Float)
    room_count: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    hotel_project: Mapped[HotelProject] = relationship(back_populates="room_types")

    def __repr__(self) -> str:
        return f"<HotelRoomType {self.room_type} {self.area_m2}m²×{self.room_count}>"


class HotelPerformanceRecord(Base):
    """Hotel occupancy, ADR, and RevPAR data per half-year period.

    hotel_project_id is nullable — a NULL value means this is a market-aggregate record
    (e.g. HCMC citywide average, or Thao Dien submarket average).

    adr_vnd  – Average Daily Rate (VND/room/night)
    revpar_vnd – Revenue Per Available Room (VND/room/night)
    """
    __tablename__ = "hotel_performance_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    hotel_project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("hotel_projects.id"))
    city_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cities.id"))
    district_id: Mapped[Optional[int]] = mapped_column(ForeignKey("districts.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("report_periods.id"))
    occupancy_rate_pct: Mapped[Optional[float]] = mapped_column(Float)
    adr_vnd: Mapped[Optional[float]] = mapped_column(Float)
    revpar_vnd: Mapped[Optional[float]] = mapped_column(Float)
    adr_usd: Mapped[Optional[float]] = mapped_column(Float)
    international_visitor_count: Mapped[Optional[int]] = mapped_column(Integer)
    domestic_visitor_count: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    hotel_project: Mapped[Optional[HotelProject]] = relationship(
        foreign_keys=[hotel_project_id], back_populates="performance_records"
    )
    city: Mapped[Optional[City]] = relationship(
        foreign_keys=[city_id], back_populates="hotel_performance_records"
    )
    district: Mapped[Optional[District]] = relationship(
        foreign_keys=[district_id], back_populates="hotel_performance_records"
    )
    period: Mapped[ReportPeriod] = relationship(back_populates="hotel_performance_records")

    def __repr__(self) -> str:
        return f"<HotelPerformanceRecord occ={self.occupancy_rate_pct}% ADR={self.adr_vnd}>"


# ---------------------------------------------------------------------------
# Land Site Analysis (Parts B-E)
# ---------------------------------------------------------------------------

class LandSite(Base):
    """Candidate land site for development evaluation.

    document_type: "land_review" | "product_proposal" | "design_guideline"
    development_role: "developer" | "investor" | "jv"
    """
    __tablename__ = "land_sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    report_group: Mapped[Optional[str]] = mapped_column(String(100))
    document_type: Mapped[Optional[str]] = mapped_column(String(30))
    city_text: Mapped[Optional[str]] = mapped_column(String(100))
    district_text: Mapped[Optional[str]] = mapped_column(String(100))
    land_area_ha: Mapped[Optional[float]] = mapped_column(Float)
    development_type: Mapped[Optional[str]] = mapped_column(String(30))
    recommended_grade: Mapped[Optional[str]] = mapped_column(String(10))
    positioning: Mapped[Optional[str]] = mapped_column(Text)
    exchange_rate_usd_vnd: Mapped[Optional[float]] = mapped_column(Float)
    total_units_target: Mapped[Optional[int]] = mapped_column(Integer)
    master_developer: Mapped[Optional[str]] = mapped_column(String(200))
    development_role: Mapped[Optional[str]] = mapped_column(String(30))
    development_concept: Mapped[Optional[str]] = mapped_column(Text)
    total_highrise_units: Mapped[Optional[int]] = mapped_column(Integer)
    total_lowrise_units: Mapped[Optional[int]] = mapped_column(Integer)
    bcr_pct: Mapped[Optional[float]] = mapped_column(Float)
    site_shape: Mapped[Optional[str]] = mapped_column(String(20))
    frontage_count: Mapped[Optional[int]] = mapped_column(Integer)
    main_road_name: Mapped[Optional[str]] = mapped_column(String(200))
    main_road_width_m: Mapped[Optional[float]] = mapped_column(Float)
    secondary_road_name: Mapped[Optional[str]] = mapped_column(String(200))
    secondary_road_width_m: Mapped[Optional[float]] = mapped_column(Float)
    distance_to_cbd_km: Mapped[Optional[float]] = mapped_column(Float)
    distance_to_cbd_min: Mapped[Optional[int]] = mapped_column(Integer)
    rental_yield_pct: Mapped[Optional[float]] = mapped_column(Float)
    pd_suggestion: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    zones: Mapped[list["SiteZone"]] = relationship(back_populates="land_site")
    planning_indicators: Mapped[list["SitePlanningIndicator"]] = relationship(back_populates="land_site")
    specifications: Mapped[list["SiteSpecification"]] = relationship(back_populates="land_site")
    nearby_facilities: Mapped[list["SiteNearbyFacility"]] = relationship(back_populates="land_site")
    swot_items: Mapped[list["SiteSwotItem"]] = relationship(back_populates="land_site")
    competitors: Mapped[list["SiteCompetitor"]] = relationship(back_populates="land_site")
    price_targets: Mapped[list["SitePriceTarget"]] = relationship(back_populates="land_site")
    target_customers: Mapped[list["SiteTargetCustomer"]] = relationship(back_populates="land_site")
    development_phases: Mapped[list["SiteDevelopmentPhase"]] = relationship(back_populates="land_site")
    views: Mapped[list["SiteView"]] = relationship(back_populates="land_site")
    recommended_projects: Mapped[list["SiteRecommendedProject"]] = relationship(back_populates="land_site")
    visual_assets: Mapped[list["ReportVisualAsset"]] = relationship(back_populates="land_site")
    design_guidelines: Mapped[list["DesignGuideline"]] = relationship(back_populates="land_site")
    development_directions: Mapped[list["DevelopmentDirection"]] = relationship(back_populates="land_site")

    def __repr__(self) -> str:
        return f"<LandSite {self.name} {self.land_area_ha}ha>"


class SiteZone(Base):
    """Internal zone within a large land site (e.g. HP 25ha Zone 1-4)."""
    __tablename__ = "site_zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    zone_code: Mapped[str] = mapped_column(String(10))
    area_ha: Mapped[Optional[float]] = mapped_column(Float)
    far: Mapped[Optional[float]] = mapped_column(Float)
    strengths: Mapped[Optional[str]] = mapped_column(Text)
    weaknesses: Mapped[Optional[str]] = mapped_column(Text)
    highrise_units_planned: Mapped[Optional[int]] = mapped_column(Integer)
    lowrise_units_planned: Mapped[Optional[int]] = mapped_column(Integer)
    key_anchor: Mapped[Optional[str]] = mapped_column(Text)
    phase_sequence: Mapped[Optional[int]] = mapped_column(Integer)
    benchmark_project: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="zones")

    def __repr__(self) -> str:
        return f"<SiteZone {self.zone_code} {self.area_ha}ha>"


class SitePlanningIndicator(Base):
    """FAR, BCR, GFA, unit counts — zone-level or site-level."""
    __tablename__ = "site_planning_indicators"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    zone_id: Mapped[Optional[int]] = mapped_column(ForeignKey("site_zones.id"))
    indicator_type: Mapped[str] = mapped_column(String(30))
    value_numeric: Mapped[Optional[float]] = mapped_column(Float)
    value_text: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="planning_indicators")

    def __repr__(self) -> str:
        return f"<SitePlanningIndicator {self.indicator_type}={self.value_numeric}>"


class SiteSpecification(Base):
    """Road infrastructure, railway, river frontage etc."""
    __tablename__ = "site_specifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    spec_type: Mapped[str] = mapped_column(String(30))
    value_text: Mapped[Optional[str]] = mapped_column(String(200))
    value_numeric: Mapped[Optional[float]] = mapped_column(Float)
    direction: Mapped[Optional[str]] = mapped_column(String(10))
    status: Mapped[Optional[str]] = mapped_column(String(30))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="specifications")

    def __repr__(self) -> str:
        return f"<SiteSpecification {self.spec_type}: {self.value_text}>"


class SiteNearbyFacility(Base):
    """Facilities within distance bands (3km/5km/10km)."""
    __tablename__ = "site_nearby_facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    facility_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(30))
    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    distance_band: Mapped[Optional[str]] = mapped_column(String(10))
    direction: Mapped[Optional[str]] = mapped_column(String(10))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="nearby_facilities")

    def __repr__(self) -> str:
        return f"<SiteNearbyFacility {self.facility_name} {self.distance_km}km>"


class SiteSwotItem(Base):
    """SWOT analysis items for a land site."""
    __tablename__ = "site_swot_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    swot_type: Mapped[str] = mapped_column(String(1))  # S / W / O / T
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[Optional[int]] = mapped_column(Integer)

    land_site: Mapped[LandSite] = relationship(back_populates="swot_items")

    def __repr__(self) -> str:
        return f"<SiteSwotItem {self.swot_type}: {self.description[:40]}>"


class SiteCompetitor(Base):
    """Competitor projects near a land site, with product-type prices and unit mix."""
    __tablename__ = "site_competitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    competitor_name: Mapped[str] = mapped_column(String(200))
    developer: Mapped[Optional[str]] = mapped_column(String(200))
    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    distance_band: Mapped[Optional[str]] = mapped_column(String(10))
    total_units: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(String(30))
    launch_date: Mapped[Optional[str]] = mapped_column(String(30))
    handover_date: Mapped[Optional[str]] = mapped_column(String(30))
    price_confidence: Mapped[Optional[str]] = mapped_column(String(20))
    product_category: Mapped[Optional[str]] = mapped_column(String(30))
    # Product-type prices (USD/m²)
    townhouse_price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    shophouse_price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    villa_price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    apt_price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    # Complex / phase info (for compact apt reviews)
    complex_area_ha: Mapped[Optional[float]] = mapped_column(Float)
    complex_total_units: Mapped[Optional[int]] = mapped_column(Integer)
    phase_code: Mapped[Optional[str]] = mapped_column(String(20))
    phase_name: Mapped[Optional[str]] = mapped_column(String(100))
    phase_area_ha: Mapped[Optional[float]] = mapped_column(Float)
    phase_units: Mapped[Optional[int]] = mapped_column(Integer)
    # Unit size info
    land_size_min: Mapped[Optional[float]] = mapped_column(Float)
    land_size_max: Mapped[Optional[float]] = mapped_column(Float)
    unit_size_min: Mapped[Optional[float]] = mapped_column(Float)
    unit_size_max: Mapped[Optional[float]] = mapped_column(Float)
    floors: Mapped[Optional[int]] = mapped_column(Integer)
    # Unit mix by bedroom type (%)
    studio_pct: Mapped[Optional[float]] = mapped_column(Float)
    br1_1wc_pct: Mapped[Optional[float]] = mapped_column(Float)
    br1_5_1wc_pct: Mapped[Optional[float]] = mapped_column(Float)
    br2_1wc_pct: Mapped[Optional[float]] = mapped_column(Float)
    br2_2wc_pct: Mapped[Optional[float]] = mapped_column(Float)
    br2_5_2wc_pct: Mapped[Optional[float]] = mapped_column(Float)
    br3_2wc_pct: Mapped[Optional[float]] = mapped_column(Float)
    # Sales absorption
    sold_units: Mapped[Optional[int]] = mapped_column(Integer)
    sold_pct: Mapped[Optional[float]] = mapped_column(Float)
    absorption_days: Mapped[Optional[int]] = mapped_column(Integer)
    absorption_note: Mapped[Optional[str]] = mapped_column(Text)
    # Price totals
    total_price_min_vnd_bil: Mapped[Optional[float]] = mapped_column(Float)
    total_price_max_vnd_bil: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="competitors")

    def __repr__(self) -> str:
        return f"<SiteCompetitor {self.competitor_name}>"


class SitePriceTarget(Base):
    """NHO recommended price targets by product type."""
    __tablename__ = "site_price_targets"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    product_type: Mapped[str] = mapped_column(String(30))
    price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    total_price_vnd_bil: Mapped[Optional[float]] = mapped_column(Float)
    unit_size_m2: Mapped[Optional[float]] = mapped_column(Float)
    unit_count: Mapped[Optional[int]] = mapped_column(Integer)
    launch: Mapped[Optional[str]] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="price_targets")

    def __repr__(self) -> str:
        return f"<SitePriceTarget {self.product_type} ${self.price_usd_m2}/m²>"


class SiteTargetCustomer(Base):
    """Target customer segments with ratios."""
    __tablename__ = "site_target_customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    segment_name: Mapped[str] = mapped_column(String(100))
    ratio_pct: Mapped[Optional[float]] = mapped_column(Float)
    purpose: Mapped[Optional[str]] = mapped_column(String(20))
    profile: Mapped[Optional[str]] = mapped_column(Text)
    target_products: Mapped[Optional[str]] = mapped_column(String(200))

    land_site: Mapped[LandSite] = relationship(back_populates="target_customers")

    def __repr__(self) -> str:
        return f"<SiteTargetCustomer {self.segment_name} {self.ratio_pct}%>"


class SiteDevelopmentPhase(Base):
    """Phase-level development strategy."""
    __tablename__ = "site_development_phases"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    phase_number: Mapped[int] = mapped_column(Integer)
    phase_name: Mapped[Optional[str]] = mapped_column(String(100))
    zone_code: Mapped[Optional[str]] = mapped_column(String(10))
    product_types: Mapped[Optional[str]] = mapped_column(String(200))
    unit_count: Mapped[Optional[int]] = mapped_column(Integer)
    launch_target: Mapped[Optional[str]] = mapped_column(String(20))
    strategy_notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="development_phases")

    def __repr__(self) -> str:
        return f"<SiteDevelopmentPhase P{self.phase_number}>"


# ---------------------------------------------------------------------------
# Part C: Case Studies & Payment Schedules
# ---------------------------------------------------------------------------

class CaseStudyProject(Base):
    """Benchmark/reference project for product proposals."""
    __tablename__ = "case_study_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_name: Mapped[str] = mapped_column(String(200))
    developer_name: Mapped[Optional[str]] = mapped_column(String(200))
    city_text: Mapped[Optional[str]] = mapped_column(String(100))
    district_text: Mapped[Optional[str]] = mapped_column(String(100))
    land_area_ha: Mapped[Optional[float]] = mapped_column(Float)
    bcr_pct: Mapped[Optional[float]] = mapped_column(Float)
    total_units: Mapped[Optional[int]] = mapped_column(Integer)
    launch_date: Mapped[Optional[str]] = mapped_column(String(30))
    handover_date: Mapped[Optional[str]] = mapped_column(String(30))
    avg_price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    positioning_concept: Mapped[Optional[str]] = mapped_column(Text)
    management_company: Mapped[Optional[str]] = mapped_column(String(200))
    security_type: Mapped[Optional[str]] = mapped_column(String(20))
    source_report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("source_reports.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    phases: Mapped[list["CaseStudyPhase"]] = relationship(back_populates="case_study_project")
    payment_schedules: Mapped[list["PaymentSchedule"]] = relationship(back_populates="case_study_project")

    def __repr__(self) -> str:
        return f"<CaseStudyProject {self.project_name}>"


class CaseStudyPhase(Base):
    """Phase/sub-zone within a case study project."""
    __tablename__ = "case_study_phases"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_study_project_id: Mapped[int] = mapped_column(ForeignKey("case_study_projects.id"))
    phase_code: Mapped[str] = mapped_column(String(10))
    phase_name: Mapped[Optional[str]] = mapped_column(String(100))
    area_ha: Mapped[Optional[float]] = mapped_column(Float)
    total_units: Mapped[Optional[int]] = mapped_column(Integer)
    launch_date: Mapped[Optional[str]] = mapped_column(String(30))
    handover_date: Mapped[Optional[str]] = mapped_column(String(30))
    sales_status: Mapped[Optional[str]] = mapped_column(String(30))
    sold_units: Mapped[Optional[int]] = mapped_column(Integer)
    sold_pct: Mapped[Optional[float]] = mapped_column(Float)
    absorption_days: Mapped[Optional[int]] = mapped_column(Integer)
    avg_price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    park_highlight: Mapped[Optional[str]] = mapped_column(String(200))
    security_type: Mapped[Optional[str]] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    case_study_project: Mapped[CaseStudyProject] = relationship(back_populates="phases")
    unit_types: Mapped[list["CaseStudyUnitType"]] = relationship(back_populates="case_study_phase")

    def __repr__(self) -> str:
        return f"<CaseStudyPhase {self.phase_code} {self.phase_name}>"


class CaseStudyUnitType(Base):
    """Unit-type breakdown within a case study phase."""
    __tablename__ = "case_study_unit_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_study_phase_id: Mapped[int] = mapped_column(ForeignKey("case_study_phases.id"))
    product_type: Mapped[str] = mapped_column(String(30))
    unit_count: Mapped[Optional[int]] = mapped_column(Integer)
    unit_ratio_pct: Mapped[Optional[float]] = mapped_column(Float)
    land_size_min_m2: Mapped[Optional[float]] = mapped_column(Float)
    land_size_max_m2: Mapped[Optional[float]] = mapped_column(Float)
    gfa_m2: Mapped[Optional[float]] = mapped_column(Float)
    floors: Mapped[Optional[int]] = mapped_column(Integer)
    br_count: Mapped[Optional[int]] = mapped_column(Integer)
    wc_count: Mapped[Optional[int]] = mapped_column(Integer)
    avg_price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    total_price_min_bil_vnd: Mapped[Optional[float]] = mapped_column(Float)
    total_price_max_bil_vnd: Mapped[Optional[float]] = mapped_column(Float)
    handover_condition: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    case_study_phase: Mapped[CaseStudyPhase] = relationship(back_populates="unit_types")

    def __repr__(self) -> str:
        return f"<CaseStudyUnitType {self.product_type} ×{self.unit_count}>"


class PaymentSchedule(Base):
    """Payment method definitions for projects or case studies."""
    __tablename__ = "payment_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    case_study_project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("case_study_projects.id"))
    method_name: Mapped[str] = mapped_column(String(100))
    total_duration_months: Mapped[Optional[int]] = mapped_column(Integer)
    unit_allocation_count: Mapped[Optional[int]] = mapped_column(Integer)
    unit_allocation_pct: Mapped[Optional[float]] = mapped_column(Float)
    deposit_amount_vnd: Mapped[Optional[float]] = mapped_column(Float)
    bank_loan_max_pct: Mapped[Optional[float]] = mapped_column(Float)
    bank_grace_months: Mapped[Optional[int]] = mapped_column(Integer)
    bank_interest_note: Mapped[Optional[str]] = mapped_column(Text)
    quick_discount_pct: Mapped[Optional[float]] = mapped_column(Float)
    standard_discount_pct: Mapped[Optional[float]] = mapped_column(Float)
    early_bird_discount_vnd: Mapped[Optional[float]] = mapped_column(Float)
    loyalty_discount_pct: Mapped[Optional[float]] = mapped_column(Float)
    free_management_months: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    case_study_project: Mapped[Optional[CaseStudyProject]] = relationship(back_populates="payment_schedules")
    installments: Mapped[list["PaymentInstallment"]] = relationship(back_populates="schedule")

    def __repr__(self) -> str:
        return f"<PaymentSchedule {self.method_name}>"


class PaymentInstallment(Base):
    """Individual payment installment within a schedule."""
    __tablename__ = "payment_installments"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("payment_schedules.id"))
    installment_number: Mapped[int] = mapped_column(Integer)
    months_from_start: Mapped[Optional[int]] = mapped_column(Integer)
    pct_of_contract: Mapped[Optional[float]] = mapped_column(Float)
    pct_type: Mapped[Optional[str]] = mapped_column(String(20))
    accumulated_pct: Mapped[Optional[float]] = mapped_column(Float)
    milestone: Mapped[Optional[str]] = mapped_column(String(30))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    schedule: Mapped[PaymentSchedule] = relationship(back_populates="installments")

    def __repr__(self) -> str:
        return f"<PaymentInstallment #{self.installment_number} {self.pct_of_contract}%>"


class DevelopmentDirection(Base):
    """Development direction proposals for product proposals."""
    __tablename__ = "development_directions"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    direction_number: Mapped[int] = mapped_column(Integer)
    direction_name: Mapped[str] = mapped_column(String(200))
    concept_keywords: Mapped[Optional[str]] = mapped_column(String(200))
    standard_amenities: Mapped[Optional[str]] = mapped_column(Text)
    premium_amenities: Mapped[Optional[str]] = mapped_column(Text)
    driving_amenities: Mapped[Optional[str]] = mapped_column(Text)
    target_positioning: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="development_directions")

    def __repr__(self) -> str:
        return f"<DevelopmentDirection #{self.direction_number} {self.direction_name}>"


class ProjectPark(Base):
    """Themed parks and landscaping facilities."""
    __tablename__ = "project_parks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    case_study_phase_id: Mapped[Optional[int]] = mapped_column(ForeignKey("case_study_phases.id"))
    land_site_id: Mapped[Optional[int]] = mapped_column(ForeignKey("land_sites.id"))
    park_name: Mapped[str] = mapped_column(String(200))
    park_theme: Mapped[Optional[str]] = mapped_column(String(100))
    area_ha: Mapped[Optional[float]] = mapped_column(Float)
    area_m2: Mapped[Optional[float]] = mapped_column(Float)
    park_type: Mapped[Optional[str]] = mapped_column(String(30))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<ProjectPark {self.park_name}>"


# ---------------------------------------------------------------------------
# Part D: Views & Visual Assets
# ---------------------------------------------------------------------------

class SiteView(Base):
    """Directional view evaluation for a land site."""
    __tablename__ = "site_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    direction: Mapped[str] = mapped_column(String(5))
    view_type: Mapped[str] = mapped_column(String(10))
    view_target: Mapped[Optional[str]] = mapped_column(String(200))
    impact_on_positioning: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="views")

    def __repr__(self) -> str:
        return f"<SiteView {self.direction} {self.view_type}>"


class SiteRecommendedProject(Base):
    """Design benchmark projects (not direct competitors)."""
    __tablename__ = "site_recommended_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    project_name: Mapped[str] = mapped_column(String(200))
    developer: Mapped[Optional[str]] = mapped_column(String(200))
    city_text: Mapped[Optional[str]] = mapped_column(String(100))
    district_text: Mapped[Optional[str]] = mapped_column(String(100))
    grade: Mapped[Optional[str]] = mapped_column(String(10))
    price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    sales_performance: Mapped[Optional[str]] = mapped_column(String(200))
    design_highlight: Mapped[Optional[str]] = mapped_column(Text)
    recommendation_reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="recommended_projects")

    def __repr__(self) -> str:
        return f"<SiteRecommendedProject {self.project_name}>"


class ReportVisualAsset(Base):
    """Visual asset metadata for report generation."""
    __tablename__ = "report_visual_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    asset_type: Mapped[str] = mapped_column(String(30))
    asset_page: Mapped[Optional[int]] = mapped_column(Integer)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    generation_method: Mapped[Optional[str]] = mapped_column(String(20))
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    generation_config: Mapped[Optional[str]] = mapped_column(Text)
    display_order: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="visual_assets")

    def __repr__(self) -> str:
        return f"<ReportVisualAsset {self.asset_type}>"


# ---------------------------------------------------------------------------
# Part E: Design Guidelines
# ---------------------------------------------------------------------------

class DesignGuideline(Base):
    """Design guideline document for a land site."""
    __tablename__ = "design_guidelines"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[int] = mapped_column(ForeignKey("land_sites.id"))
    option_scenario: Mapped[Optional[str]] = mapped_column(String(50))
    design_concept: Mapped[Optional[str]] = mapped_column(Text)
    orientation_constraints: Mapped[Optional[str]] = mapped_column(Text)
    topography_notes: Mapped[Optional[str]] = mapped_column(Text)
    buffer_requirements: Mapped[Optional[str]] = mapped_column(Text)
    premiumization_strategy: Mapped[Optional[str]] = mapped_column(Text)
    facade_direction: Mapped[Optional[str]] = mapped_column(Text)
    pd_review_date: Mapped[Optional[str]] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    land_site: Mapped[LandSite] = relationship(back_populates="design_guidelines")
    product_specs: Mapped[list["DesignProductSpec"]] = relationship(back_populates="design_guideline")
    case_studies: Mapped[list["DesignCaseStudy"]] = relationship(back_populates="design_guideline")

    def __repr__(self) -> str:
        return f"<DesignGuideline {self.option_scenario}>"


class DesignProductSpec(Base):
    """Product specifications within a design guideline option."""
    __tablename__ = "design_product_specs"

    id: Mapped[int] = mapped_column(primary_key=True)
    design_guideline_id: Mapped[int] = mapped_column(ForeignKey("design_guidelines.id"))
    product_type: Mapped[str] = mapped_column(String(30))
    ratio_pct: Mapped[Optional[float]] = mapped_column(Float)
    floors: Mapped[Optional[int]] = mapped_column(Integer)
    unit_count: Mapped[Optional[int]] = mapped_column(Integer)
    unit_size_min_m2: Mapped[Optional[float]] = mapped_column(Float)
    unit_size_max_m2: Mapped[Optional[float]] = mapped_column(Float)
    typical_size_m2: Mapped[Optional[float]] = mapped_column(Float)
    target_price_usd_m2: Mapped[Optional[float]] = mapped_column(Float)
    target_price_vnd_mil: Mapped[Optional[float]] = mapped_column(Float)
    total_price_vnd_bil: Mapped[Optional[float]] = mapped_column(Float)
    expected_launch: Mapped[Optional[str]] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    design_guideline: Mapped[DesignGuideline] = relationship(back_populates="product_specs")

    def __repr__(self) -> str:
        return f"<DesignProductSpec {self.product_type} {self.ratio_pct}%>"


class DesignCaseStudy(Base):
    """Design/architecture reference projects within a design guideline."""
    __tablename__ = "design_case_studies"

    id: Mapped[int] = mapped_column(primary_key=True)
    design_guideline_id: Mapped[int] = mapped_column(ForeignKey("design_guidelines.id"))
    reference_category: Mapped[str] = mapped_column(String(30))
    project_name: Mapped[str] = mapped_column(String(200))
    developer: Mapped[Optional[str]] = mapped_column(String(200))
    city_text: Mapped[Optional[str]] = mapped_column(String(100))
    district_text: Mapped[Optional[str]] = mapped_column(String(100))
    land_area_ha: Mapped[Optional[float]] = mapped_column(Float)
    total_units: Mapped[Optional[int]] = mapped_column(Integer)
    floors: Mapped[Optional[int]] = mapped_column(Integer)
    design_style: Mapped[Optional[str]] = mapped_column(String(50))
    design_highlight: Mapped[Optional[str]] = mapped_column(Text)
    reference_purpose: Mapped[Optional[str]] = mapped_column(String(30))
    product_allocation_notes: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    design_guideline: Mapped[DesignGuideline] = relationship(back_populates="case_studies")

    def __repr__(self) -> str:
        return f"<DesignCaseStudy {self.project_name}>"


class SportParkFacility(Base):
    """Sport park facility inventory for benchmarking."""
    __tablename__ = "sport_park_facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    land_site_id: Mapped[Optional[int]] = mapped_column(ForeignKey("land_sites.id"))
    case_study_name: Mapped[Optional[str]] = mapped_column(String(200))
    park_area_ha: Mapped[Optional[float]] = mapped_column(Float)
    zone_structure: Mapped[Optional[str]] = mapped_column(String(100))
    clubhouse_count: Mapped[Optional[int]] = mapped_column(Integer)
    tennis_courts: Mapped[Optional[int]] = mapped_column(Integer)
    badminton_courts: Mapped[Optional[int]] = mapped_column(Integer)
    mini_basketball_courts: Mapped[Optional[int]] = mapped_column(Integer)
    mini_football_courts: Mapped[Optional[int]] = mapped_column(Integer)
    kids_playgrounds: Mapped[Optional[int]] = mapped_column(Integer)
    pool_count: Mapped[Optional[int]] = mapped_column(Integer)
    kids_pool_count: Mapped[Optional[int]] = mapped_column(Integer)
    jacuzzi_count: Mapped[Optional[int]] = mapped_column(Integer)
    outdoor_gym_count: Mapped[Optional[int]] = mapped_column(Integer)
    picnic_lawn_count: Mapped[Optional[int]] = mapped_column(Integer)
    bbq_count: Mapped[Optional[int]] = mapped_column(Integer)
    jogging_track_count: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<SportParkFacility {self.case_study_name or self.land_site_id}>"
