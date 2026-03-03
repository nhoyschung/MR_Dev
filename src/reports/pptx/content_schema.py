"""TypedDict handoff contract between pptx-content-writer, ko-translator, and pptx-builder.

All agent communication uses these schemas. Language-agnostic structure;
the 'language' field on SlideContentManifest indicates EN or KO.
"""

from typing import Any, Literal, Optional, TypedDict


class KpiItem(TypedDict):
    label: str           # "Active Projects"
    value: str           # "47"
    delta: Optional[str]  # "+5 vs H2 2024"
    color: Optional[str]  # "green" | "red" | "amber" | "blue"


class CoverSlide(TypedDict):
    index: int
    type: Literal["cover"]
    title: str
    subtitle: str
    city: str
    period: str
    report_type: str
    date: str


class KpiDashboardSlide(TypedDict):
    index: int
    type: Literal["kpi_dashboard"]
    slide_title: str
    kpis: list[KpiItem]
    note: str  # Expert narrative paragraph


class TableSlide(TypedDict):
    index: int
    type: Literal["table"]
    title: str
    headers: list[str]
    rows: list[list[str]]
    caption: Optional[str]         # Expert commentary below table
    grade_col_index: Optional[int]  # Column index to apply grade colours


class ChartSlide(TypedDict):
    index: int
    type: Literal["chart"]
    title: str
    chart_type: str      # "price_trend" | "grade_distribution" | "radar" | "supply_demand" | "price_comparison"
    chart_params: dict[str, Any]   # Parameters passed to the corresponding create_*_figure()
    caption: str
    right_panel_text: Optional[str]  # Analyst commentary alongside chart


class SwotSlide(TypedDict):
    index: int
    type: Literal["swot"]
    title: str
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]


class ConclusionSlide(TypedDict):
    index: int
    type: Literal["conclusion"]
    title: str
    verdict: str            # "HIGHLY VIABLE" | "MODERATELY VIABLE" | "REQUIRES STUDY"
    bullets: list[str]      # 3-5 key findings
    badge_label: str        # Text on the verdict badge
    badge_color: str        # "green" | "amber" | "red"


class SectionDividerSlide(TypedDict):
    index: int
    type: Literal["section_divider"]
    number: str     # "01", "02", etc.
    title: str
    subtitle: str


class SlideContentManifest(TypedDict):
    job_id: str
    report_type: str   # "market_briefing" | "project_profile" | "land_review" | "competitor"
                       # | "unit_type_analysis" | "enhanced_land_review" | "product_proposal"
                       # | "compact_land_review" | "design_guideline"
    language: str      # "en" | "ko"
    params: dict[str, Any]   # Original query params (city, year, half, etc.)
    slides: list[dict]        # List of the typed slides above
