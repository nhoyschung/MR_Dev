# MR-System v2: Land Evaluation & Development Proposal Pipeline
## System Design Addendum — Based on 5 Output Reports Analysis

> Reports analyzed:
> - HP-35ha Proposal (109p) — Full development proposal
> - 240ha Bac Ninh Land Review (43p) — Large-scale land review
> - BD Potential Land Review (17p) — Mid-scale land assessment
> - 25ha Duong Kinh Land Review (12p) — Standard land review
> - Hai Phong 3 Land SWOT (1p) — Quick screening comparison

---

## 1. DISCOVERY: THE COMPLETE DECISION PIPELINE

The 5 Output reports reveal a **4-stage decision pipeline** that NHO-PD follows:

```
STAGE 0: LAND SOURCING
  Input:  Broker offers, internal sourcing, market opportunities
  Output: Candidate land parcels with basic info
  ↓
STAGE 1: QUICK SCREENING (1-page SWOT)
  Input:  2-5 candidate land parcels
  Output: Side-by-side SWOT comparison + Priority ranking (1st/2nd/3rd)
  Decision: Select top parcels for deep evaluation
  Template: 1 page
  ↓
STAGE 2: FULL LAND REVIEW (12-43 pages)
  Input:  Single high-priority land parcel
  Output: Multi-layer analysis + Conditional Go/No-Go recommendation
  Decision: Proceed to proposal OR reject
  Template: 12p (small) / 17p (medium) / 43p (large 240ha+)
  ↓
STAGE 3: DEVELOPMENT PROPOSAL (100+ pages)
  Input:  Approved land + positioning strategy
  Output: Product mix, pricing, phasing, concepts, case studies
  Decision: Proceed to feasibility/acquisition OR reject
  Template: ~110p (includes 70+ pages of case studies)
```

### Key Insight: Conclusion-First Structure
All reports use an **executive-first** format — the recommendation/conclusion appears at the BEGINNING (pages 2-3), with supporting analysis following. This is designed for C-suite consumption.

---

## 2. REPORT TYPE COMPARISON

| Dimension | SWOT Screening | Land Review (Small) | Land Review (Large) | Dev. Proposal |
|-----------|---------------|-------------------|-------------------|---------------|
| Pages | 1 | 12 | 43 | 109 |
| Parcels | 3-5 compared | 1 deep-dive | 1 deep-dive | 1 deep-dive |
| Purpose | Screen & rank | Feasibility assess | Feasibility assess | Product/strategy |
| Conclusion | Priority ranking | Conditional Go/No-Go | Go/No-Go + strategy | Full product plan |
| Market data | Price summary | 5-7 competitors | 15+ competitors | 7+ competitors + 3 case studies |
| Customer analysis | No | Segmentation table | Full segmentation | Living/Tenant split with ratios |
| Product mix | No | Referenced from FS | Suggested | Full zone-by-zone specification |
| Pricing | Selling price only | Competitor benchmark | Proposed pricing | Proposed by product type |
| Phasing | No | No | Suggested | 4-phase plan with +/- |
| Case studies | No | No | Limited | 73% of report (75+ pages) |
| Dev. concepts | No | No | No | 3 alternative concepts |
| Time to produce | Hours | 1-2 days | 3-5 days | 1-2 weeks |

---

## 3. DATA TYPES UNIQUE TO LAND EVALUATION

### 3.1 Site Physical Assessment
- Land area (ha/m2)
- Zone subdivision (parcel divisions by road grid)
- Shape regularity (regular/irregular)
- FAR (Floor Area Ratio) by sub-zone
- Waterfront/river exposure
- High-voltage line crossings (220kV, 110kV) + safety corridors
- Adjacent land features (sport land, industrial park, canals)
- Current access points (count, width in meters)
- Surrounding views (positive/negative: river vs industrial park)
- Topography (flat, sloped, flood risk)

### 3.2 Development Condition Assessment
- Per-zone strengths/weaknesses
- Infrastructure readiness per zone
- Developability timeline (NOW vs WAIT)
- Land compensation requirements (existing households)
- Government land return obligations (sport land, public facilities)
- Power line constraint mitigation options

### 3.3 Customer Segmentation (Land-Specific)
- Living purpose % vs Investment purpose % (by product type)
- Low-rise: ~30% living / ~70% investor
- High-rise: ~50% living / ~50% investor
- Customer origin geography (local %, foreign %, other regions %)
- Foreign breakdown by nationality (Japanese, Korean, Chinese, Taiwanese)
- Occupation profiles (IP experts, business owners, civil servants)
- Age ranges per segment
- Key decision factors (ranked)

### 3.4 Development Proposal Data
- Proposed product mix by zone (unit types, counts, sizes)
- Proposed pricing by product type (USD/m2, Bil VND/unit)
- Development concept names and themes
- Amenity framework (Standard/Premium/Driving tiers)
- Phasing sequence with anchor facility assignments
- Phase-level pros/cons assessment
- Benchmark project references

### 3.5 Case Study Depth (10-Section Template)
Each benchmark project analyzed with:
1. Project Location & Regional Connectivity
2. Project Summary (developer, area, products, pricing, status)
3. Sales Points (slogan, marketing positioning)
4. Master Plan (phasing, themed zones, circulation)
5. Facilities (complex-level + phase-level)
6. Unit Ratio (product distribution with dimensions)
7. Unit Layout (floor plans with L/W ratios, yard counts)
8. Unit Finishing (handover specs)
9. Payment Schedule (installment terms, discounts, bank support)
10. Operation (management company, fees, services)

---

## 4. NEW AGENT ARCHITECTURE FOR LAND EVALUATION

### 4.1 Agent Overview

```
┌────────────────────────────────────────────────────────────┐
│           LAND EVALUATION AGENT SYSTEM                      │
│                                                              │
│  STAGE 1 AGENTS (Screening)                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐         │
│  │ Location    │ │ Quick       │ │ SWOT         │         │
│  │ Scorer      │ │ Market      │ │ Generator    │         │
│  │             │ │ Scanner     │ │ & Ranker     │         │
│  └─────────────┘ └─────────────┘ └──────────────┘         │
│                                                              │
│  STAGE 2 AGENTS (Full Review)                               │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐         │
│  │ Macro       │ │ Site        │ │ Competitor   │         │
│  │ Research    │ │ Evaluator   │ │ Intelligence │         │
│  │ Agent       │ │             │ │ Agent        │         │
│  └─────────────┘ └─────────────┘ └──────────────┘         │
│  ┌─────────────┐ ┌─────────────┐                           │
│  │ Customer    │ │ Risk        │                           │
│  │ Segmenter   │ │ Assessor    │                           │
│  └─────────────┘ └─────────────┘                           │
│                                                              │
│  STAGE 3 AGENTS (Proposal)                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐         │
│  │ Concept     │ │ Product Mix │ │ Phasing      │         │
│  │ Designer    │ │ Optimizer   │ │ Strategist   │         │
│  └─────────────┘ └─────────────┘ └──────────────┘         │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐         │
│  │ Pricing     │ │ Case Study  │ │ Proposal     │         │
│  │ Calibrator  │ │ Matcher     │ │ Assembler    │         │
│  └─────────────┘ └─────────────┘ └──────────────┘         │
└────────────────────────────────────────────────────────────┘
```

### 4.2 Agent Specifications

#### `land-screener` — Quick SWOT Screening Agent
```yaml
name: land-screener
purpose: Rapid assessment of 2-5 land parcels
inputs:
  - Land parcels (area, location, basic info)
  - Radius for competitor search (km)
process:
  1. Auto-retrieve location data (distances to CBD, airports, EZs)
  2. Scan competitor database within radius
  3. Check infrastructure status (existing/planned roads)
  4. Check zoning/legal constraints
  5. Generate SWOT bullets per parcel
  6. Apply priority ranking criteria
outputs:
  - 1-page SWOT comparison matrix
  - Priority ranking with justification
implicit_ranking_criteria:
  - Can develop NOW vs need to WAIT (highest weight)
  - Road access quality (direct frontage vs future roads)
  - Land use flexibility (mixed-use vs restricted)
  - Price competitiveness vs competitors
  - Legal/government risk level
  - Land size for phasing capability
```

#### `land-reviewer` — Full Land Review Agent
```yaml
name: land-reviewer
purpose: Comprehensive single-parcel assessment
inputs:
  - Land parcel details
  - SWOT screening results (if available)
process:
  1. Macro analysis: city planning context, district development orientation
  2. Location analysis: infrastructure mapping, distance calculations
  3. Competitor deep analysis: 5-15 projects within radius
  4. Site micro analysis: zone subdivision, FAR, constraints
  5. Per-zone strengths/weaknesses
  6. SWOT synthesis
  7. Customer segmentation
  8. Conditional Go/No-Go recommendation
outputs:
  - 12-43 page land review (size-dependent)
  - Structured data for database storage
  - Conditional recommendation with asterisked further assessments
```

#### `proposal-builder` — Development Proposal Agent
```yaml
name: proposal-builder
purpose: Full development proposal with product strategy
inputs:
  - Approved land review
  - Market analysis data
  - Competitor benchmarks
  - Case study library access
process:
  1. Generate 2-3 development direction concepts
  2. Design amenity framework (Standard/Premium/Driving)
  3. Optimize product mix by zone
  4. Calibrate pricing vs competitors
  5. Design phasing strategy with anchor assignments
  6. Select and format relevant case studies
  7. Assemble full proposal document
outputs:
  - 100+ page development proposal
  - Product specification tables
  - Phasing plan with rationale
  - 3+ case study sheets (10 sections each)
```

#### `case-study-librarian` — Benchmark Case Study Agent
```yaml
name: case-study-librarian
purpose: Maintain and retrieve benchmark project case studies
inputs:
  - Project parameters for matching (scale, product type, location tier, positioning)
process:
  1. Search case study database for similar projects
  2. Rank by relevance (scale similarity, product overlap, location tier match)
  3. Format selected case studies in 10-section template
  4. Extract applicable strategic lessons
outputs:
  - Formatted 10-section case study sheets
  - Strategic lesson summaries
  - Pricing/phasing/product progression data
```

---

## 5. NEW SKILLS FOR LAND EVALUATION

### `/land-screen {parcel1} {parcel2} ...`
```
Purpose: Quick SWOT comparison of multiple land parcels
Output: 1-page ranking matrix
```

### `/land-review {parcel_id}`
```
Purpose: Full land review for a single parcel
Output: 12-43 page structured analysis
```

### `/dev-proposal {parcel_id}`
```
Purpose: Full development proposal
Output: 100+ page proposal with case studies
```

### `/find-benchmark {scale_ha} {product_types} {location_tier}`
```
Purpose: Find similar case study projects
Output: Ranked list of comparable projects with relevance scores
```

### `/zone-subdivide {parcel_boundary} {constraints}`
```
Purpose: Subdivide a land parcel into development zones
Output: Zone map with areas, FAR, constraints per zone
```

### `/price-position {product_type} {district} {grade}`
```
Purpose: Calibrate pricing against competitors
Output: Recommended price range with benchmark justification
```

---

## 6. DATABASE SCHEMA ADDITIONS

```sql
-- =============================================
-- LAND PARCELS
-- =============================================

CREATE TABLE land_parcels (
    id                  SERIAL PRIMARY KEY,
    parcel_name         VARCHAR(200),
    parcel_code         VARCHAR(50),
    district_id         INTEGER REFERENCES districts(id),
    market_id           INTEGER REFERENCES markets(id),
    total_area_ha       DECIMAL(10,2),
    total_area_m2       DECIMAL(15,2),
    shape_regularity    VARCHAR(20),           -- regular, irregular
    current_use         VARCHAR(100),          -- agricultural, vacant, mixed
    acquisition_status  VARCHAR(30),           -- sourcing, screening, reviewing, proposed, acquired, rejected
    coordinates         VARCHAR(100),          -- lat/lng
    address             TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE parcel_zones (
    id                  SERIAL PRIMARY KEY,
    parcel_id           INTEGER REFERENCES land_parcels(id),
    zone_number         INTEGER,
    zone_name           VARCHAR(50),           -- "Zone 1", "Zone A"
    area_ha             DECIMAL(10,2),
    zone_type           VARCHAR(50),           -- mixed_use, residential, commercial
    far                 DECIMAL(5,2),          -- Floor Area Ratio
    strengths           TEXT,                  -- JSON array
    weaknesses          TEXT,                  -- JSON array
    notes               TEXT
);

CREATE TABLE parcel_constraints (
    id                  SERIAL PRIMARY KEY,
    parcel_id           INTEGER REFERENCES land_parcels(id),
    constraint_type     VARCHAR(50),           -- high_voltage, flood_risk, noise, view_negative
    details             TEXT,                  -- "220kV crossing Zone 3"
    severity            VARCHAR(20),           -- high, medium, low
    mitigation          TEXT                   -- "Green belt buffer"
);

CREATE TABLE parcel_access_points (
    id                  SERIAL PRIMARY KEY,
    parcel_id           INTEGER REFERENCES land_parcels(id),
    road_name           VARCHAR(200),
    road_type           VARCHAR(30),           -- existing, planned
    road_width_m        DECIMAL(6,2),
    lanes               INTEGER,
    status              VARCHAR(30),           -- completed, under_construction, planning
    expected_completion VARCHAR(20),
    direction           VARCHAR(20)            -- north, south, east, west
);

-- =============================================
-- LAND EVALUATIONS
-- =============================================

CREATE TABLE swot_screenings (
    id                  SERIAL PRIMARY KEY,
    screening_date      DATE,
    analyst             VARCHAR(100),
    parcels_compared    INTEGER,               -- how many parcels in this screening
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE swot_entries (
    id                  SERIAL PRIMARY KEY,
    screening_id        INTEGER REFERENCES swot_screenings(id),
    parcel_id           INTEGER REFERENCES land_parcels(id),
    priority_rank       INTEGER,               -- 1st, 2nd, 3rd
    strengths           TEXT,                  -- JSON array of bullets
    weaknesses          TEXT,
    opportunities       TEXT,
    threats             TEXT,
    conclusion          TEXT,                  -- justification for ranking
    go_signal           VARCHAR(20)            -- go_immediate, conditional_go, no_go
);

CREATE TABLE land_reviews (
    id                  SERIAL PRIMARY KEY,
    parcel_id           INTEGER REFERENCES land_parcels(id),
    review_date         DATE,
    analyst             VARCHAR(100),
    review_type         VARCHAR(20),           -- quick, standard, comprehensive
    total_pages         INTEGER,
    recommendation      VARCHAR(30),           -- go, conditional_go, no_go
    conditions          TEXT,                  -- asterisked further assessments needed
    positioning_summary TEXT,
    strategy_summary    TEXT,
    file_path           VARCHAR(500),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE land_review_factors (
    id                  SERIAL PRIMARY KEY,
    review_id           INTEGER REFERENCES land_reviews(id),
    factor_name         VARCHAR(100),          -- location, infrastructure, market_gap, etc.
    assessment          VARCHAR(20),           -- positive, negative, neutral
    score               INTEGER,               -- 1-5 if scored
    detail              TEXT
);

-- =============================================
-- DEVELOPMENT PROPOSALS
-- =============================================

CREATE TABLE development_proposals (
    id                  SERIAL PRIMARY KEY,
    parcel_id           INTEGER REFERENCES land_parcels(id),
    review_id           INTEGER REFERENCES land_reviews(id),
    proposal_date       DATE,
    proposal_name       VARCHAR(200),
    concept_selected    VARCHAR(200),          -- chosen development direction
    total_units         INTEGER,
    lowrise_units       INTEGER,
    highrise_units      INTEGER,
    lowrise_ratio_pct   DECIMAL(5,2),
    total_phases        INTEGER,
    exchange_rate       DECIMAL(10,2),
    file_path           VARCHAR(500),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE development_concepts (
    id                  SERIAL PRIMARY KEY,
    proposal_id         INTEGER REFERENCES development_proposals(id),
    concept_number      INTEGER,               -- 1, 2, 3
    concept_name        VARCHAR(200),          -- "Expandable Wellness-Driven New CBD"
    theme               TEXT,
    description         TEXT,
    framework           TEXT                   -- Live/Work/Play/Stay Well etc.
);

CREATE TABLE amenity_framework (
    id                  SERIAL PRIMARY KEY,
    proposal_id         INTEGER REFERENCES development_proposals(id),
    tier                VARCHAR(20),           -- standard, premium, driving
    category            VARCHAR(50),           -- live, play, work, stay_well
    facility_name       VARCHAR(200),
    description         TEXT
);

CREATE TABLE proposed_product_mix (
    id                  SERIAL PRIMARY KEY,
    proposal_id         INTEGER REFERENCES development_proposals(id),
    zone_id             INTEGER REFERENCES parcel_zones(id),
    product_type        VARCHAR(30),           -- TH, SH, Semi-Villa, Single-Villa, Commercial-Apt, Social-Apt
    unit_count          INTEGER,
    land_size_m2        DECIMAL(8,2),
    gfa_m2              DECIMAL(8,2),
    floors              INTEGER,
    proposed_price_usd  DECIMAL(10,2),
    proposed_price_bil_vnd DECIMAL(10,2),
    handover_condition  VARCHAR(100),
    notes               TEXT
);

CREATE TABLE phasing_plans (
    id                  SERIAL PRIMARY KEY,
    proposal_id         INTEGER REFERENCES development_proposals(id),
    phase_number        INTEGER,
    zone_id             INTEGER REFERENCES parcel_zones(id),
    phase_name          VARCHAR(100),
    pros                TEXT,                  -- JSON array
    cons                TEXT,                  -- JSON array
    anchor_facilities   TEXT,                  -- JSON array
    target_buyers       TEXT,
    strategy_notes      TEXT,
    estimated_launch    VARCHAR(20)
);

-- =============================================
-- CASE STUDY LIBRARY
-- =============================================

CREATE TABLE case_studies (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    case_study_date     DATE,
    total_pages         INTEGER,
    relevance_tags      TEXT,                  -- JSON: ["township", "hai_phong", "wellness"]
    key_lessons         TEXT,                  -- JSON array
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE case_study_sections (
    id                  SERIAL PRIMARY KEY,
    case_study_id       INTEGER REFERENCES case_studies(id),
    section_number      INTEGER,               -- 1-10
    section_name        VARCHAR(50),           -- location, summary, sales_point, etc.
    content             TEXT,                  -- structured JSON or markdown
    data_points         TEXT                   -- JSON of extracted metrics
);

-- =============================================
-- CUSTOMER SEGMENTATION (Land-Specific)
-- =============================================

CREATE TABLE land_customer_segments (
    id                  SERIAL PRIMARY KEY,
    parcel_id           INTEGER REFERENCES land_parcels(id),
    segment_name        VARCHAR(100),          -- "Customer Living", "Customer Tenant"
    purpose             VARCHAR(30),           -- living, investment, mixed
    percentage          DECIMAL(5,2),
    product_type        VARCHAR(30),           -- low_rise, high_rise
    age_range           VARCHAR(20),
    origin_geography    TEXT,                  -- JSON: {"local": 50, "foreign": 40, "other": 10}
    foreign_breakdown   TEXT,                  -- JSON: {"japanese": 30, "korean": 25, ...}
    occupations         TEXT,                  -- JSON array
    characteristics     TEXT,                  -- JSON array
    decision_factors    TEXT                   -- JSON array (ranked)
);

-- =============================================
-- PRICE CHANGE FACTORS (from Sales Price Report)
-- =============================================

CREATE TABLE price_change_factors (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    period              VARCHAR(20),           -- "2024-H1"
    direction           VARCHAR(10),           -- increase, decrease
    factor_location     BOOLEAN DEFAULT FALSE,
    factor_supply_shortage BOOLEAN DEFAULT FALSE,
    factor_construction BOOLEAN DEFAULT FALSE,
    factor_urban_planning BOOLEAN DEFAULT FALSE,
    factor_competitive_price BOOLEAN DEFAULT FALSE,
    factor_neighborhood BOOLEAN DEFAULT FALSE,
    factor_old_project  BOOLEAN DEFAULT FALSE,
    factor_legal        BOOLEAN DEFAULT FALSE,
    factor_bank_loan    BOOLEAN DEFAULT FALSE,
    factor_oversupply   BOOLEAN DEFAULT FALSE,
    factor_management   BOOLEAN DEFAULT FALSE,
    factor_other        TEXT,
    detail_narrative    TEXT
);

-- =============================================
-- PROJECT PRICE HISTORY (Semi-Annual Snapshots)
-- =============================================

CREATE TABLE project_price_history (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    period              VARCHAR(20) NOT NULL,  -- "2024-H1", "2023-H2"
    price_type          VARCHAR(20),           -- primary, secondary
    price_usd_m2        DECIMAL(10,2),
    price_vnd_m2        DECIMAL(15,2),
    hoh_change_pct      DECIMAL(5,2),
    grade_at_period     VARCHAR(10),           -- grade based on current price
    data_source         VARCHAR(200),
    collection_date     DATE
);

CREATE TABLE project_grade_history (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    grade_primary       VARCHAR(10),           -- grade at original launch price
    grade_secondary     VARCHAR(10),           -- grade at current secondary price
    migration_direction VARCHAR(10),           -- up, down, stable
    migration_steps     INTEGER,               -- how many grade levels moved
    as_of_period        VARCHAR(20)
);

-- =============================================
-- DEVELOPER SALES POLICIES
-- =============================================

CREATE TABLE developer_sales_policies (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    policy_period       VARCHAR(20),
    max_deposit_pct     DECIMAL(5,2),
    first_payment_max_pct DECIMAL(5,2),
    payment_until_handover_max_pct DECIMAL(5,2),
    discount_pct        DECIMAL(5,2),
    grace_period_months INTEGER,
    interest_support_months INTEGER,
    free_mgmt_months    INTEGER,
    interior_gift       BOOLEAN DEFAULT FALSE,
    policy_description  TEXT
);
```

---

## 7. COMPLETE SYSTEM ARCHITECTURE (Updated v2)

```
MR-SYSTEM COMPLETE PIPELINE
============================

[DATA COLLECTION LAYER]
  ├── Web Scrapers (batdongsan, cafeland, developer sites)
  ├── News Crawlers (vnexpress, cafef, dantri, vneconomy)
  ├── PDF Ingestors (CBRE, Savills, DKRA reports)
  ├── Government Data (planning docs, regulations, stats)
  └── Field Data Entry (site visits, construction progress)
         │
         ▼
[DATA STORAGE LAYER]
  ├── Structured DB (PostgreSQL) ── 50+ tables
  │   ├── Markets, Zones, Districts
  │   ├── Projects (34+ seeded, growing)
  │   ├── Pricing (time-series, semi-annual)
  │   ├── Land Parcels & Evaluations
  │   ├── Case Study Library
  │   ├── Customer Segments
  │   └── Infrastructure, Regulations, News
  ├── Document Store (PDFs, images, floor plans)
  └── Vector DB (semantic search across all reports)
         │
         ▼
[ANALYSIS LAYER — TWO TRACKS]
  │
  ├── TRACK A: MARKET INTELLIGENCE
  │   ├── market-analyzer ────→ Market overview, trends
  │   ├── competitor-benchmarker → Project comparison
  │   ├── price-tracker ──────→ Semi-annual price snapshots
  │   └── strategy-advisor ───→ Strategic recommendations
  │
  └── TRACK B: LAND EVALUATION
      ├── land-screener ──────→ SWOT screening (Stage 1)
      ├── land-reviewer ──────→ Full land review (Stage 2)
      ├── proposal-builder ───→ Development proposal (Stage 3)
      ├── case-study-librarian → Benchmark matching
      ├── concept-designer ───→ Development concepts
      ├── product-mix-optimizer → Unit mix & pricing
      └── phasing-strategist ─→ Phase sequence & anchors
         │
         ▼
[REPORT GENERATION LAYER]
  ├── Template Engine (Jinja2)
  ├── Chart Generator (matplotlib/plotly)
  ├── PPTX Generator (python-pptx)
  ├── Multi-language (KO/EN/VI)
  └── Report Types:
      ├── Market Analysis Report (NHO-PD style, 250-450p)
      ├── Sales Price Analysis (NHO-PD style, 66p)
      ├── SWOT Screening (1p)
      ├── Land Review (12-43p)
      └── Development Proposal (100+p)
```

---

## 8. SKILLS SUMMARY (Complete List)

### Market Intelligence Skills
| Skill | Purpose | Output |
|-------|---------|--------|
| `/vn-market-briefing` | Daily/weekly market update | Briefing document |
| `/project-profile {name}` | Single project deep-dive | 11-section profile |
| `/competitor-compare {p1} {p2}` | Side-by-side comparison | Comparison matrix |
| `/zone-analysis {city} {zone}` | Zone-level market analysis | Zone report |
| `/price-strategy {params}` | Price positioning advice | Pricing recommendation |
| `/price-track {city}` | Semi-annual price snapshot | Price change report |
| `/data-update` | Trigger data collection | Update summary |
| `/full-report {city} {year}` | Full market report | 250-450p report |

### Land Evaluation Skills
| Skill | Purpose | Output |
|-------|---------|--------|
| `/land-screen {parcels}` | Quick SWOT comparison | 1-page ranking |
| `/land-review {parcel}` | Full land assessment | 12-43p review |
| `/dev-proposal {parcel}` | Development proposal | 100+p proposal |
| `/find-benchmark {params}` | Case study matching | Ranked similar projects |
| `/zone-subdivide {parcel}` | Parcel subdivision | Zone map with specs |
| `/price-position {params}` | Pricing calibration | Price range + benchmarks |

---

## 9. IMPLEMENTATION PRIORITY (Updated)

### Sprint 1: Foundation (Week 1-2)
- [ ] Database setup with full schema (50+ tables)
- [ ] Seed data from 9 analyzed reports (34+ projects, 5 markets)
- [ ] Project structure & CLAUDE.md

### Sprint 2: Data Collection (Week 3-4)
- [ ] batdongsan.com.vn scraper
- [ ] News crawler (vnexpress, cafef)
- [ ] PDF report ingestor
- [ ] Data validation pipeline

### Sprint 3: Market Intelligence Agents (Week 5-6)
- [ ] data-collector agent
- [ ] market-analyzer agent
- [ ] competitor-benchmarker agent
- [ ] price-tracker agent

### Sprint 4: Land Evaluation Agents (Week 7-8)
- [ ] land-screener agent (SWOT)
- [ ] land-reviewer agent
- [ ] case-study-librarian agent

### Sprint 5: Proposal & Strategy (Week 9-10)
- [ ] proposal-builder agent
- [ ] concept-designer agent
- [ ] product-mix-optimizer agent
- [ ] strategy-advisor agent

### Sprint 6: Report Generation (Week 11-12)
- [ ] Template engine for all 5 report types
- [ ] Chart generation
- [ ] PPTX export
- [ ] Multi-language support

### Sprint 7: Skills & Integration (Week 13-14)
- [ ] All 14 skills implementation
- [ ] End-to-end pipeline testing
- [ ] Validation against original NHO-PD reports
