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
