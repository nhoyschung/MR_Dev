"""Tests for unit-type price structure analysis: queries, charts, report generation."""

import math

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import (
    Base, City, District, Project, UnitType, PriceRecord, ReportPeriod,
)


@pytest.fixture
def db_session():
    """In-memory SQLite with Star View (inverted) + Emerald 68 (normal) test data."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect", lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close())
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    # Reference data
    city = City(name_en="Binh Duong", region="South")
    session.add(city)
    session.flush()

    district = District(name_en="Thuan An", city_id=city.id, district_type="suburban")
    session.add(district)
    session.flush()

    period = ReportPeriod(year=2025, half="H2")
    session.add(period)
    session.flush()

    # Star View (INVERTED: larger units cost MORE per m2)
    sv = Project(name="Starview", district_id=district.id, grade_primary="H-II")
    session.add(sv)
    session.flush()

    sv_units = [
        ("1.5BR", 45.2, 2615),
        ("2BR", 51.4, 3003),
        ("2.5BR", 66.9, 2954),
        ("3BR", 72.0, 3368),
    ]
    for type_name, area, price_usd in sv_units:
        ut = UnitType(project_id=sv.id, type_name=type_name, net_area_m2=area)
        session.add(ut)
        session.flush()
        pr = PriceRecord(
            project_id=sv.id, unit_type_id=ut.id, period_id=period.id,
            price_usd_per_m2=price_usd, price_vnd_per_m2=price_usd * 25500,
            data_source="nho_internal",
        )
        session.add(pr)

    # Emerald 68 (NORMAL: smaller units cost more per m2)
    em = Project(name="The Emerald 68", district_id=district.id, grade_primary="H-II")
    session.add(em)
    session.flush()

    em_units = [
        ("1BR", 34.8, 2718),
        ("1.5BR", 45.7, 2490),
        ("2BR", 67.8, 2478),
        ("3BR", 81.9, 2545),
    ]
    for type_name, area, price_usd in em_units:
        ut = UnitType(project_id=em.id, type_name=type_name, net_area_m2=area)
        session.add(ut)
        session.flush()
        pr = PriceRecord(
            project_id=em.id, unit_type_id=ut.id, period_id=period.id,
            price_usd_per_m2=price_usd, price_vnd_per_m2=price_usd * 25500,
            data_source="nho_internal",
        )
        session.add(pr)

    # Single-unit project (edge case)
    single = Project(name="SingleUnit", district_id=district.id)
    session.add(single)
    session.flush()
    ut_single = UnitType(project_id=single.id, type_name="2BR", net_area_m2=60.0)
    session.add(ut_single)
    session.flush()
    PriceRecord(
        project_id=single.id, unit_type_id=ut_single.id, period_id=period.id,
        price_usd_per_m2=2000, price_vnd_per_m2=51000000,
        data_source="nho_internal",
    )
    session.add(PriceRecord(
        project_id=single.id, unit_type_id=ut_single.id, period_id=period.id,
        price_usd_per_m2=2000, price_vnd_per_m2=51000000,
        data_source="nho_internal",
    ))

    session.commit()
    yield session
    session.close()


# ── get_unit_type_prices ────────────────────────────────────────────

class TestGetUnitTypePrices:
    def test_returns_list(self, db_session: Session):
        from src.db.queries import get_unit_type_prices
        sv = db_session.query(Project).filter_by(name="Starview").one()
        result = get_unit_type_prices(db_session, sv.id)
        assert isinstance(result, list)
        assert len(result) == 4

    def test_sorted_by_area(self, db_session: Session):
        from src.db.queries import get_unit_type_prices
        sv = db_session.query(Project).filter_by(name="Starview").one()
        result = get_unit_type_prices(db_session, sv.id)
        areas = [r["net_area_m2"] for r in result]
        assert areas == sorted(areas)

    def test_empty_for_unknown(self, db_session: Session):
        from src.db.queries import get_unit_type_prices
        result = get_unit_type_prices(db_session, 99999)
        assert result == []


# ── get_unit_type_price_variance ────────────────────────────────────

class TestGetUnitTypePriceVariance:
    def test_starview_inverted(self, db_session: Session):
        from src.db.queries import get_unit_type_price_variance
        sv = db_session.query(Project).filter_by(name="Starview").one()
        var = get_unit_type_price_variance(db_session, sv.id)
        assert var is not None
        assert var["is_inverted"] is True
        assert var["price_area_correlation"] > 0.3

    def test_emerald_normal(self, db_session: Session):
        from src.db.queries import get_unit_type_price_variance
        em = db_session.query(Project).filter_by(name="The Emerald 68").one()
        var = get_unit_type_price_variance(db_session, em.id)
        assert var is not None
        assert var["is_inverted"] is False
        assert var["price_area_correlation"] < 0.3

    def test_cv_positive(self, db_session: Session):
        from src.db.queries import get_unit_type_price_variance
        sv = db_session.query(Project).filter_by(name="Starview").one()
        var = get_unit_type_price_variance(db_session, sv.id)
        assert var["cv_pct"] > 0

    def test_insufficient_data_returns_none(self, db_session: Session):
        from src.db.queries import get_unit_type_price_variance
        single = db_session.query(Project).filter_by(name="SingleUnit").one()
        var = get_unit_type_price_variance(db_session, single.id)
        # SingleUnit has only 1 unit type, so returns None
        assert var is None


# ── compare_unit_type_structures ────────────────────────────────────

class TestCompareUnitTypeStructures:
    def test_returns_dict_structure(self, db_session: Session):
        from src.db.queries import compare_unit_type_structures
        sv = db_session.query(Project).filter_by(name="Starview").one()
        em = db_session.query(Project).filter_by(name="The Emerald 68").one()
        result = compare_unit_type_structures(db_session, sv.id, [em.id])
        assert "subject" in result
        assert "competitors" in result
        assert "anomalies" in result
        assert "market_avg_cv_pct" in result

    def test_detects_inverted_anomaly(self, db_session: Session):
        from src.db.queries import compare_unit_type_structures
        sv = db_session.query(Project).filter_by(name="Starview").one()
        em = db_session.query(Project).filter_by(name="The Emerald 68").one()
        result = compare_unit_type_structures(db_session, sv.id, [em.id])
        has_inverted = any("INVERTED" in a for a in result["anomalies"])
        assert has_inverted

    def test_subject_cv_premium_positive(self, db_session: Session):
        from src.db.queries import compare_unit_type_structures
        sv = db_session.query(Project).filter_by(name="Starview").one()
        em = db_session.query(Project).filter_by(name="The Emerald 68").one()
        result = compare_unit_type_structures(db_session, sv.id, [em.id])
        # Star View has higher CV than Emerald 68 (inverted structure)
        assert result["subject_cv_premium"] > 0


# ── Chart factories ─────────────────────────────────────────────────

class TestChartFactories:
    def test_grouped_bar_figure(self):
        from src.reports.charts import create_unit_type_grouped_bar_figure
        import matplotlib.pyplot as plt
        data = [
            {"project_name": "A", "unit_types": [
                {"type_name": "1BR", "price_usd_per_m2": 2500},
                {"type_name": "2BR", "price_usd_per_m2": 2300},
            ]},
            {"project_name": "B", "unit_types": [
                {"type_name": "1BR", "price_usd_per_m2": 2700},
                {"type_name": "2BR", "price_usd_per_m2": 2400},
            ]},
        ]
        fig = create_unit_type_grouped_bar_figure(data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_variance_comparison_figure(self):
        from src.reports.charts import create_variance_comparison_figure
        import matplotlib.pyplot as plt
        data = [
            {"project_name": "Subject", "cv_pct": 12.5, "is_subject": True},
            {"project_name": "Comp A", "cv_pct": 5.2, "is_subject": False},
        ]
        fig = create_variance_comparison_figure(data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_area_price_scatter_figure(self):
        from src.reports.charts import create_area_price_scatter_figure
        import matplotlib.pyplot as plt
        data = [
            {"project_name": "A", "points": [
                {"net_area_m2": 45, "price_usd_per_m2": 2600, "type_name": "1.5BR"},
                {"net_area_m2": 72, "price_usd_per_m2": 3300, "type_name": "3BR"},
            ]},
        ]
        fig = create_area_price_scatter_figure(data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ── Report generation ───────────────────────────────────────────────

class TestReportGeneration:
    def test_context_assembly(self, db_session: Session):
        from src.reports.unit_type_analysis import _assemble_unit_type_context
        ctx = _assemble_unit_type_context(
            db_session, "Starview", ["The Emerald 68"], 2025, "H2"
        )
        assert ctx is not None
        assert ctx["subject_name"] == "Starview"
        assert len(ctx["subject_prices"]) == 4
        assert ctx["subject_variance"]["is_inverted"] is True

    def test_md_rendering(self, db_session: Session):
        from src.reports.unit_type_analysis import generate_unit_type_analysis
        md = generate_unit_type_analysis(
            db_session, "Starview", ["The Emerald 68"], 2025, "H2"
        )
        assert md is not None
        assert "INVERTED" in md
        assert "Starview" in md

    def test_returns_none_unknown_project(self, db_session: Session):
        from src.reports.unit_type_analysis import generate_unit_type_analysis
        result = generate_unit_type_analysis(
            db_session, "NonExistentProject", [], 2025, "H2"
        )
        assert result is None


# ── Edge cases ──────────────────────────────────────────────────────

class TestEdgeCases:
    def test_single_unit_type_returns_none(self, db_session: Session):
        from src.db.queries import get_unit_type_price_variance
        single = db_session.query(Project).filter_by(name="SingleUnit").one()
        assert get_unit_type_price_variance(db_session, single.id) is None

    def test_empty_chart_returns_none(self):
        from src.reports.charts import create_unit_type_grouped_bar_figure
        assert create_unit_type_grouped_bar_figure([]) is None

    def test_empty_variance_chart_returns_none(self):
        from src.reports.charts import create_variance_comparison_figure
        assert create_variance_comparison_figure([]) is None

    def test_empty_scatter_returns_none(self):
        from src.reports.charts import create_area_price_scatter_figure
        assert create_area_price_scatter_figure([]) is None
