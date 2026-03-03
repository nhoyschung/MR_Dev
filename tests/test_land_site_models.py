"""Integration tests for land site models, seeders, and report engines (Parts B-E)."""

import matplotlib
matplotlib.use("Agg")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import (
    Base, LandSite, SiteZone, SiteCompetitor, SitePriceTarget,
    SiteTargetCustomer, SiteSpecification, SiteSwotItem,
    SiteDevelopmentPhase, SiteView, SiteRecommendedProject,
    CaseStudyProject, CaseStudyPhase, CaseStudyUnitType,
    DesignGuideline, DesignProductSpec, DesignCaseStudy,
    SportParkFacility, ReportVisualAsset, DevelopmentDirection,
)


@pytest.fixture
def db_session():
    """In-memory SQLite with sample land site data for all 4 document types."""
    engine = create_engine("sqlite:///:memory:")
    event.listen(engine, "connect",
                 lambda c, _: c.cursor().execute("PRAGMA foreign_keys=ON") or c.cursor().close())
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    # --- HP 25ha (enhanced land review) ---
    hp25 = LandSite(
        name="HP_25ha_Duong_Kinh",
        document_type="land_review",
        city_text="Hai Phong", district_text="Duong Kinh",
        land_area_ha=25.0, development_type="mixed-use",
        recommended_grade="M-I",
        positioning="Hybrid Urban Township",
        total_units_target=3691,
        exchange_rate_usd_vnd=25500,
    )
    session.add(hp25)
    session.flush()

    # Zones
    for code, area, far in [("1", 9.01, 12.8), ("2", 5.93, 12.8), ("3", 3.10, 12.8), ("4", 8.66, 4.2)]:
        session.add(SiteZone(land_site_id=hp25.id, zone_code=code, area_ha=area, far=far,
                             strengths=f"Zone {code} strength", weaknesses=f"Zone {code} weakness"))

    # Competitors
    session.add(SiteCompetitor(land_site_id=hp25.id, competitor_name="VGC P1",
                               developer="Vinhomes", distance_km=8, distance_band="8km",
                               total_units=641, townhouse_price_usd_m2=3352, status="on-sales"))
    session.add(SiteCompetitor(land_site_id=hp25.id, competitor_name="Ramond Urbaniz",
                               developer="Ramond", distance_km=4.2, distance_band="5km",
                               total_units=438, townhouse_price_usd_m2=2553))

    # Price targets
    session.add(SitePriceTarget(land_site_id=hp25.id, product_type="townhouse",
                                price_usd_m2=1844, unit_count=569, unit_size_m2=90, launch="2027"))
    session.add(SitePriceTarget(land_site_id=hp25.id, product_type="shophouse",
                                price_usd_m2=2142, unit_count=256))

    # Target customers
    session.add(SiteTargetCustomer(land_site_id=hp25.id, segment_name="Low-rise Living",
                                   ratio_pct=30, purpose="living", target_products="TH, Villa"))

    # Specifications
    session.add(SiteSpecification(land_site_id=hp25.id, spec_type="main_road",
                                  value_text="DT402", value_numeric=28, status="planning"))

    # SWOT
    session.add(SiteSwotItem(land_site_id=hp25.id, swot_type="S", description="River frontage"))
    session.add(SiteSwotItem(land_site_id=hp25.id, swot_type="W", description="Weak infrastructure"))

    # Development phases
    session.add(SiteDevelopmentPhase(land_site_id=hp25.id, phase_number=1,
                                    phase_name="Launch Phase", zone_code="4",
                                    product_types="TH, SH", unit_count=500, launch_target="2027"))

    session.flush()

    # --- HP 35ha (product proposal) ---
    hp35 = LandSite(
        name="HP_35ha_Duong_Kinh",
        document_type="product_proposal",
        city_text="Hai Phong", district_text="Duong Kinh",
        land_area_ha=37.39, development_type="mixed-use",
        development_concept="Wellness-Driven New CBD",
        total_units_target=4950,
        total_highrise_units=4000, total_lowrise_units=950,
    )
    session.add(hp35)
    session.flush()

    for code, area, hr, lr, seq in [("1", 11.76, None, 325, 1), ("2", 5.81, 1000, 100, 2)]:
        session.add(SiteZone(land_site_id=hp35.id, zone_code=code, area_ha=area,
                             highrise_units_planned=hr, lowrise_units_planned=lr,
                             phase_sequence=seq, key_anchor=f"Zone {code} anchor"))

    # Development direction
    session.add(DevelopmentDirection(
        land_site_id=hp35.id, direction_number=1,
        direction_name="Expandable Wellness-Driven New CBD",
        concept_keywords="Live-Work-Play-Stay Well",
    ))

    session.flush()

    # --- Di An 2.3ha (compact land review) ---
    dian = LandSite(
        name="Di_An_2.3ha",
        document_type="land_review",
        city_text="Binh Duong", district_text="Di An",
        land_area_ha=2.3, development_type="apartment",
        recommended_grade="H-II",
        total_units_target=1854,
        site_shape="regular", frontage_count=2,
        main_road_name="NR1A", main_road_width_m=28,
        distance_to_cbd_km=22.8, distance_to_cbd_min=42,
        rental_yield_pct=4.7,
        pd_suggestion="Strong development potential.",
    )
    session.add(dian)
    session.flush()

    # Competitors with unit mix
    session.add(SiteCompetitor(
        land_site_id=dian.id, competitor_name="The Gio Riverside",
        developer="An Gia", distance_km=1.6, distance_band="3km",
        phase_code="P1", phase_units=1470, apt_price_usd_m2=2134,
        studio_pct=9.5, br1_1wc_pct=81, br2_1wc_pct=9.5,
        sold_pct=89, absorption_days=1, absorption_note="89% on launch day",
    ))

    # Views
    session.add(SiteView(land_site_id=dian.id, direction="W", view_type="negative",
                         view_target="Binh An Textile IP"))
    session.add(SiteView(land_site_id=dian.id, direction="E", view_type="positive",
                         view_target="Hung Kings Temple"))

    # Recommended projects
    session.add(SiteRecommendedProject(
        land_site_id=dian.id, project_name="The Gio Gio Nam",
        developer="An Gia", grade="M-I", price_usd_m2=2134,
        sales_performance="89% on launch day",
    ))

    # Price targets
    session.add(SitePriceTarget(land_site_id=dian.id, product_type="apartment",
                                price_usd_m2=2260, unit_count=1803, unit_size_m2=61))

    session.flush()

    # --- HP 7.2ha (design guideline) ---
    hp72 = LandSite(
        name="HP_7.2ha_Kien_An",
        document_type="design_guideline",
        city_text="Hai Phong", district_text="Kien An",
        land_area_ha=7.2, development_type="mixed-use",
        total_units_target=1063,
        main_road_name="Tran Thanh Ngo Street",
    )
    session.add(hp72)
    session.flush()

    # Design guideline
    dg = DesignGuideline(
        land_site_id=hp72.id,
        option_scenario="Option 3",
        design_concept="Back to Mountain, Facing River",
        orientation_constraints="Avoid west-facing units",
        buffer_requirements="Pagoda buffer zone",
        premiumization_strategy="Boutique condominiums positioning",
        facade_direction="Japandi + Sculptural",
    )
    session.add(dg)
    session.flush()

    # Product specs
    session.add(DesignProductSpec(design_guideline_id=dg.id, product_type="TH/SH",
                                 ratio_pct=20, floors=3, target_price_usd_m2=3000))
    session.add(DesignProductSpec(design_guideline_id=dg.id, product_type="commercial_apt",
                                 ratio_pct=50, floors=7, unit_count=613,
                                 target_price_usd_m2=1600))
    session.add(DesignProductSpec(design_guideline_id=dg.id, product_type="social_apt",
                                 ratio_pct=30, floors=7, unit_count=296,
                                 target_price_usd_m2=700))

    # Design case studies
    session.add(DesignCaseStudy(design_guideline_id=dg.id, reference_category="masterplan",
                                project_name="Golden Point", design_style="neoclassical"))
    session.add(DesignCaseStudy(design_guideline_id=dg.id, reference_category="commercial_apt",
                                project_name="The Sculptura", design_style="Sculptural"))

    # Competitors by category
    session.add(SiteCompetitor(land_site_id=hp72.id, competitor_name="Star Central",
                               product_category="townhouse", distance_km=3.3,
                               phase_units=157, townhouse_price_usd_m2=3398))
    session.add(SiteCompetitor(land_site_id=hp72.id, competitor_name="An Zen Residence",
                               product_category="commercial_apt", distance_km=4.47,
                               phase_units=887, apt_price_usd_m2=1241))

    # Sport park facilities
    session.add(SportParkFacility(case_study_name="Vinhomes Grand Park",
                                  park_area_ha=1.3, tennis_courts=2, badminton_courts=3))
    session.add(SportParkFacility(case_study_name="The Fulton",
                                  park_area_ha=1.9, tennis_courts=1, badminton_courts=4,
                                  clubhouse_count=1))

    session.flush()

    # --- Case Study Project ---
    cs = CaseStudyProject(
        project_name="Vinhomes Golden City",
        developer_name="Vinhomes",
        city_text="Hai Phong",
        land_area_ha=240.57,
        bcr_pct=27, total_units=4800,
        positioning_concept="City of Ecological Parks",
    )
    session.add(cs)
    session.flush()

    phase = CaseStudyPhase(
        case_study_project_id=cs.id, phase_code="P1", phase_name="Starlight Park",
        area_ha=53.4, total_units=1206, sold_pct=94, absorption_days=60,
    )
    session.add(phase)
    session.flush()

    session.add(CaseStudyUnitType(
        case_study_phase_id=phase.id, product_type="TH",
        unit_count=641, avg_price_usd_m2=3352,
    ))

    session.commit()
    yield session
    session.close()


# ── Model CRUD Tests ──────────────────────────────────────────────────────

class TestLandSiteCRUD:
    def test_land_sites_created(self, db_session: Session):
        sites = db_session.query(LandSite).all()
        assert len(sites) == 4

    def test_hp25_has_zones(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="HP_25ha_Duong_Kinh").one()
        assert len(site.zones) == 4
        assert sum(z.area_ha for z in site.zones) == pytest.approx(26.7, abs=0.1)

    def test_hp25_has_competitors(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="HP_25ha_Duong_Kinh").one()
        assert len(site.competitors) == 2

    def test_hp25_has_price_targets(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="HP_25ha_Duong_Kinh").one()
        assert len(site.price_targets) == 2

    def test_hp25_has_swot(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="HP_25ha_Duong_Kinh").one()
        assert len(site.swot_items) == 2

    def test_hp35_has_directions(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="HP_35ha_Duong_Kinh").one()
        assert len(site.development_directions) == 1

    def test_dian_has_views(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="Di_An_2.3ha").one()
        assert len(site.views) == 2
        positive = [v for v in site.views if v.view_type == "positive"]
        assert len(positive) == 1

    def test_dian_competitor_unit_mix(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="Di_An_2.3ha").one()
        comp = site.competitors[0]
        assert comp.br1_1wc_pct == 81
        assert comp.absorption_days == 1

    def test_dian_recommended_projects(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="Di_An_2.3ha").one()
        assert len(site.recommended_projects) == 1

    def test_hp72_design_guideline(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="HP_7.2ha_Kien_An").one()
        assert len(site.design_guidelines) == 1
        dg = site.design_guidelines[0]
        assert dg.option_scenario == "Option 3"
        assert len(dg.product_specs) == 3
        assert len(dg.case_studies) == 2

    def test_product_spec_ratios_sum_100(self, db_session: Session):
        site = db_session.query(LandSite).filter_by(name="HP_7.2ha_Kien_An").one()
        specs = site.design_guidelines[0].product_specs
        total = sum(s.ratio_pct for s in specs)
        assert total == 100

    def test_sport_park_facilities(self, db_session: Session):
        parks = db_session.query(SportParkFacility).all()
        assert len(parks) == 2
        fulton = next(p for p in parks if p.case_study_name == "The Fulton")
        assert fulton.clubhouse_count == 1

    def test_case_study_hierarchy(self, db_session: Session):
        cs = db_session.query(CaseStudyProject).filter_by(
            project_name="Vinhomes Golden City"
        ).one()
        assert len(cs.phases) == 1
        phase = cs.phases[0]
        assert phase.phase_code == "P1"
        assert len(phase.unit_types) == 1
        assert phase.unit_types[0].avg_price_usd_m2 == 3352


# ── Report Engine Tests ────────────────────────────────────────────────────

class TestEnhancedLandReview:
    def test_context_assembly(self, db_session: Session):
        from src.reports.enhanced_land_review import _assemble_enhanced_site_context
        site = db_session.query(LandSite).filter_by(name="HP_25ha_Duong_Kinh").one()
        ctx = _assemble_enhanced_site_context(db_session, site.id)
        assert ctx is not None
        assert ctx["site_name"] == "HP_25ha_Duong_Kinh"
        assert len(ctx["zones"]) == 4
        assert len(ctx["competitors"]) == 2
        assert len(ctx["price_targets"]) == 2

    def test_md_rendering(self, db_session: Session):
        from src.reports.enhanced_land_review import generate_enhanced_land_review
        site = db_session.query(LandSite).filter_by(name="HP_25ha_Duong_Kinh").one()
        md = generate_enhanced_land_review(db_session, site.id)
        assert md is not None
        assert "HP_25ha_Duong_Kinh" in md
        assert "VGC P1" in md

    def test_returns_none_for_invalid(self, db_session: Session):
        from src.reports.enhanced_land_review import generate_enhanced_land_review
        assert generate_enhanced_land_review(db_session, 99999) is None


class TestProductProposal:
    def test_context_assembly(self, db_session: Session):
        from src.reports.product_proposal import _assemble_proposal_context
        site = db_session.query(LandSite).filter_by(name="HP_35ha_Duong_Kinh").one()
        ctx = _assemble_proposal_context(db_session, site.id)
        assert ctx is not None
        assert ctx["development_concept"] == "Wellness-Driven New CBD"
        assert len(ctx["zones"]) == 2
        assert len(ctx["development_directions"]) == 1
        assert len(ctx["case_studies"]) >= 1

    def test_md_rendering(self, db_session: Session):
        from src.reports.product_proposal import generate_product_proposal
        site = db_session.query(LandSite).filter_by(name="HP_35ha_Duong_Kinh").one()
        md = generate_product_proposal(db_session, site.id)
        assert md is not None
        assert "HP_35ha_Duong_Kinh" in md
        assert "Wellness-Driven New CBD" in md

    def test_returns_none_for_invalid(self, db_session: Session):
        from src.reports.product_proposal import generate_product_proposal
        assert generate_product_proposal(db_session, 99999) is None


class TestCompactLandReview:
    def test_context_assembly(self, db_session: Session):
        from src.reports.compact_land_review import _assemble_compact_review_context
        site = db_session.query(LandSite).filter_by(name="Di_An_2.3ha").one()
        ctx = _assemble_compact_review_context(db_session, site.id)
        assert ctx is not None
        assert ctx["pd_suggestion"] == "Strong development potential."
        assert len(ctx["competitors"]) == 1
        assert ctx["competitors"][0]["unit_mix"]["1BR-1WC"] == 81
        assert len(ctx["views"]) == 2
        assert len(ctx["recommended_projects"]) == 1

    def test_md_rendering(self, db_session: Session):
        from src.reports.compact_land_review import generate_compact_land_review
        site = db_session.query(LandSite).filter_by(name="Di_An_2.3ha").one()
        md = generate_compact_land_review(db_session, site.id)
        assert md is not None
        assert "Di_An_2.3ha" in md
        assert "The Gio Riverside" in md

    def test_returns_none_for_invalid(self, db_session: Session):
        from src.reports.compact_land_review import generate_compact_land_review
        assert generate_compact_land_review(db_session, 99999) is None


class TestDesignGuideline:
    def test_context_assembly(self, db_session: Session):
        from src.reports.design_guideline import _assemble_design_guideline_context
        site = db_session.query(LandSite).filter_by(name="HP_7.2ha_Kien_An").one()
        ctx = _assemble_design_guideline_context(db_session, site.id)
        assert ctx is not None
        assert ctx["design_concept"] == "Back to Mountain, Facing River"
        assert len(ctx["product_specs"]) == 3
        assert "masterplan" in ctx["case_studies_by_category"]
        assert len(ctx["competitors_by_category"]) >= 2
        assert len(ctx["sport_parks"]) == 2

    def test_md_rendering(self, db_session: Session):
        from src.reports.design_guideline import generate_design_guideline
        site = db_session.query(LandSite).filter_by(name="HP_7.2ha_Kien_An").one()
        md = generate_design_guideline(db_session, site.id)
        assert md is not None
        assert "HP_7.2ha_Kien_An" in md
        assert "Japandi" in md

    def test_returns_none_no_guideline(self, db_session: Session):
        from src.reports.design_guideline import _assemble_design_guideline_context
        # HP 25ha has no design guideline
        site = db_session.query(LandSite).filter_by(name="HP_25ha_Duong_Kinh").one()
        assert _assemble_design_guideline_context(db_session, site.id) is None

    def test_returns_none_for_invalid(self, db_session: Session):
        from src.reports.design_guideline import generate_design_guideline
        assert generate_design_guideline(db_session, 99999) is None


# ── Chart Tests ────────────────────────────────────────────────────────────

class TestNewCharts:
    def test_phase_price_progression(self):
        import matplotlib.pyplot as plt
        from src.reports.charts import create_phase_price_progression_figure
        data = [
            {"phase_code": "P1", "townhouse_usd": 3352},
            {"phase_code": "P2", "townhouse_usd": 3837},
            {"phase_code": "P3", "townhouse_usd": 4219},
        ]
        fig = create_phase_price_progression_figure(data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_phase_price_empty(self):
        from src.reports.charts import create_phase_price_progression_figure
        assert create_phase_price_progression_figure([]) is None

    def test_zone_product_mix(self):
        import matplotlib.pyplot as plt
        from src.reports.charts import create_zone_product_mix_figure
        data = [
            {"zone_code": "1", "highrise_units": 0, "lowrise_units": 325},
            {"zone_code": "2", "highrise_units": 1000, "lowrise_units": 100},
        ]
        fig = create_zone_product_mix_figure(data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_competitor_distance_band(self):
        import matplotlib.pyplot as plt
        from src.reports.charts import create_competitor_distance_band_figure
        data = [
            {"name": "VGC P1", "distance_km": 8, "price_usd": 3352, "units": 641},
            {"name": "Ramond", "distance_km": 4.2, "price_usd": 2553, "units": 438},
        ]
        fig = create_competitor_distance_band_figure(data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_competitor_unit_mix(self):
        import matplotlib.pyplot as plt
        from src.reports.charts import create_competitor_unit_mix_figure
        data = [
            {"name": "The Gio", "unit_mix": {"Studio": 9.5, "1BR-1WC": 81, "2BR-1WC": 9.5}},
            {"name": "Bcons", "unit_mix": {"1BR-1WC": 5.9, "2BR-2WC": 88.2}},
        ]
        fig = create_competitor_unit_mix_figure(data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_absorption_timeline(self):
        import matplotlib.pyplot as plt
        from src.reports.charts import create_absorption_timeline_figure
        data = [
            {"name": "The Gio", "sold_pct": 89, "absorption_note": "89% day 1"},
            {"name": "Elysian", "sold_pct": 93, "absorption_note": "93% in 12m"},
        ]
        fig = create_absorption_timeline_figure(data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_all_empty_charts_return_none(self):
        from src.reports.charts import (
            create_zone_product_mix_figure,
            create_competitor_distance_band_figure,
            create_competitor_unit_mix_figure,
            create_absorption_timeline_figure,
        )
        assert create_zone_product_mix_figure([]) is None
        assert create_competitor_distance_band_figure([]) is None
        assert create_competitor_unit_mix_figure([]) is None
        assert create_absorption_timeline_figure([]) is None


# ── Visual Generator Tests ─────────────────────────────────────────────────

class TestVisualGenerators:
    def test_competitor_map(self):
        from src.reports.visuals.competitor_map import generate_competitor_map
        data = generate_competitor_map(
            site_name="Test Site",
            competitors=[
                {"name": "Comp A", "distance_km": 3, "price_usd": 2000, "units": 500},
                {"name": "Comp B", "distance_km": 7, "price_usd": 3000, "units": 1000},
            ],
        )
        assert isinstance(data, bytes)
        assert len(data) > 1000  # Valid PNG

    def test_swot_diagram(self):
        from src.reports.visuals.swot_diagram import generate_swot_diagram
        data = generate_swot_diagram(
            strengths=["River frontage", "Good access"],
            weaknesses=["Far from center"],
            opportunities=["Merger event"],
            threats=["Competitor pricing"],
        )
        assert isinstance(data, bytes)
        assert len(data) > 1000

    def test_site_analysis_diagram(self):
        from src.reports.visuals.site_analysis_diagram import generate_site_analysis_diagram
        data = generate_site_analysis_diagram(
            site_name="Di An 2.3ha",
            views=[
                {"direction": "W", "view_type": "negative", "view_target": "Industrial Park"},
                {"direction": "E", "view_type": "positive", "view_target": "River"},
            ],
        )
        assert isinstance(data, bytes)
        assert len(data) > 1000
