# MR-System Architecture & Workflow
**Vietnam Real Estate Market Research — Technical Architecture**

> Version: Sprint 9 | Updated: 2026-02

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Data Flow — End to End](#2-data-flow--end-to-end)
3. [PDF Ingestion Pipeline](#3-pdf-ingestion-pipeline)
4. [Web Scraping Pipeline](#4-web-scraping-pipeline)
5. [Database Layer](#5-database-layer)
6. [Analysis & Query Pipeline](#6-analysis--query-pipeline)
7. [Agent Architecture](#7-agent-architecture)
8. [Slash Command Architecture](#8-slash-command-architecture)
9. [Report Generation Pipeline](#9-report-generation-pipeline)
10. [Component Dependency Map](#10-component-dependency-map)
11. [Module Reference](#11-module-reference)

---

## 1. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        MR-SYSTEM                                     │
│                 Vietnam Real Estate Intelligence                      │
└──────────────────────────────────────────────────────────────────────┘

  DATA SOURCES                   PROCESSING                 OUTPUT
  ─────────────                  ──────────                 ──────

  ┌─────────────┐                ┌──────────────────────┐   ┌──────────────────┐
  │ NHO-PD PDF  │──────────────► │  PDF Ingestion       │   │ Market Briefing  │
  │ Reports     │                │  Pipeline            │   │ Project Profile  │
  │ (1,200+ pg) │                │  (collectors/)       │   │ Zone Analysis    │
  └─────────────┘                └──────────┬───────────┘   │ Price Trends     │
                                            │               │ Competitor Bench │
  ┌─────────────┐                           ▼               │ Land Review      │
  │ BDS.com.vn  │──────────────► ┌──────────────────────┐   └────────┬─────────┘
  │ Web Data    │                │  Web Scraping        │            │
  │ (live mkt)  │                │  Pipeline            │            │
  └─────────────┘                │  (scrapers/)         │   ┌────────▼─────────┐
                                 └──────────┬───────────┘   │  Claude Code     │
  ┌─────────────┐                           │               │  Slash Commands  │
  │ Seed JSON   │──────────────► ┌──────────▼───────────┐   │  /vn-market-...  │
  │ Files       │                │                      │   │  /project-...    │
  │ (data/seed/)│                │  SQLite Database     │   │  /competitor-... │
  └─────────────┘                │  (22 tables)         │   │  /zone-...       │
                                 │  data/mr_system.db   │   │  /price-check    │
                                 │                      │   │  /db-query       │
                                 └──────────┬───────────┘   │  /land-review    │
                                            │               └────────┬─────────┘
                                            │                        │
                                            └────────────────────────┘
                                                      ▲
                                            ┌─────────┴────────┐
                                            │  AI Agents        │
                                            │  data-extractor   │
                                            │  market-analyzer  │
                                            │  competitor-bench │
                                            └──────────────────┘
```

---

## 2. Data Flow — End to End

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     COMPLETE DATA FLOW                                   │
└─────────────────────────────────────────────────────────────────────────┘

  INPUT                 EXTRACT              VALIDATE            STORE
  ──────                ───────              ────────            ─────

  PDF Report ──► PyMuPDF  ──► Raw Text ──► data-extractor  ──► JSON
                                                agent
                                                  │
                                                  ▼
                                         Seed JSON Files
                                         (data/seed/*.json)
                                                  │
                                                  ▼
  Seed JSON ────────────────────────────► Seeder Pipeline ──► SQLite DB
  (reference data)                        (seeders/)           22 tables


  BDS Website ──► Playwright ──► HTML ──► CSS Selectors ──► Pydantic ──┐
                  Browser                 (parsers.py)    Validation    │
                                                                        │
                                                          ┌─────────────▼────┐
                                                          │  scraped_listings │
                                                          │  (staging table)  │
                                                          └─────────┬─────────┘
                                                                    │
                                                          ┌─────────▼─────────┐
                                                          │  ProjectMatcher    │
                                                          │  (fuzzy matching)  │
                                                          └─────────┬──────────┘
                                                                    │
                                                          ┌─────────▼──────────┐
                                                          │   price_records     │
                                                          │   (after promote)   │
                                                          └─────────────────────┘


  USER QUERY ──► Slash Command ──► Agent ──► SQLAlchemy ──► DB Query ──► Report
```

---

## 3. PDF Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PDF INGESTION PIPELINE                                │
└─────────────────────────────────────────────────────────────────────────┘

  TRIGGER: New PDF file detected
  (manual, batch scan, or file watcher)

  ┌──────────────┐
  │  PDF File    │
  │  (.pdf)      │
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────────────────────────────────────┐
  │  STAGE 1: FILE DETECTION                             │
  │  ─────────────────────                               │
  │  cli_ingest_pdf.py OR cli_scan_folder.py             │
  │  OR watcher.py (inotify-style file system watch)     │
  │                                                      │
  │  → Checks file size and extension                    │
  │  → Deduplicates against source_reports table         │
  │  → Assigns ingestion job ID                          │
  └──────────────────────────┬───────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────┐
  │  STAGE 2: TEXT EXTRACTION                            │
  │  ────────────────────────                            │
  │  pdf_extractor.py (PyMuPDF / fitz)                   │
  │                                                      │
  │  → Extracts text page-by-page                        │
  │  → Computes confidence score (text density)          │
  │  → Saves extracted text to                           │
  │    user_resources/D_colect/extracted/                │
  │  → Records metadata via pdf_metadata.py              │
  └──────────────────────────┬───────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────┐
  │  STAGE 3: EXTRACTION PASSES                          │
  │  ──────────────────────────                          │
  │  src/extractors/                                     │
  │                                                      │
  │  Pass 1: market_pass_extractor.py                    │
  │    → Projects, developers, supply metrics            │
  │                                                      │
  │  Pass 2: price_pass_extractor.py                     │
  │    → Price tables, grade ranges, period prices       │
  │                                                      │
  │  Pass 3: casestudy_extractor.py                      │
  │    → Unit types, blocks, facilities, sales points    │
  │                                                      │
  │  Pass 4: land_review_extractor.py (if applicable)    │
  │    → Infrastructure, regulatory, feasibility data    │
  └──────────────────────────┬───────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────┐
  │  STAGE 4: VALIDATION (data-extractor agent)          │
  │  ──────────────────────────────────────────          │
  │  .claude/agents/data-extractor.md                    │
  │                                                      │
  │  → Maps extracted text to seed schemas               │
  │  → Validates required fields                         │
  │  → Resolves city/district foreign keys               │
  │  → Outputs seed-compatible JSON                      │
  └──────────────────────────┬───────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────┐
  │  STAGE 5: SEEDING                                    │
  │  ────────────────                                    │
  │  src/seeders/ (dependency-ordered)                   │
  │                                                      │
  │  Order:                                              │
  │  cities → districts → wards                          │
  │  → report_periods → grade_definitions                │
  │  → developers → projects                             │
  │  → project_blocks → unit_types                       │
  │  → price_records → price_change_factors              │
  │  → supply_records → sales_statuses                   │
  │  → project_facilities → project_sales_points         │
  │  → competitor_comparisons                            │
  │  → market_segment_summaries                          │
  │  → district_metrics                                  │
  │  → source_reports → data_lineage                     │
  └──────────────────────────────────────────────────────┘
```

---

## 4. Web Scraping Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WEB SCRAPING PIPELINE                                 │
└─────────────────────────────────────────────────────────────────────────┘

  COMMAND: python -m src.scrapers.cli_scrape projects --city hcmc

  ┌───────────────────────────────────────────────────────┐
  │  SCRAPER CONFIGURATION                                │
  │  config.py                                           │
  │                                                      │
  │  → BDS base URL                                      │
  │  → City slugs (tp-hcm, ha-noi, binh-duong, da-nang) │
  │  → Rate limits (12 RPM, 2-5s delay)                  │
  │  → User agent pool (5 browser strings)               │
  │  → Viewport range (1280-1480 x 900-1080)             │
  └──────────────────────────┬────────────────────────────┘
                             │
                             ▼
  ┌───────────────────────────────────────────────────────┐
  │  BROWSER MANAGER                                      │
  │  browser.py (Playwright)                              │
  │                                                      │
  │  Anti-detection:                                      │
  │  → Randomize viewport on each session                │
  │  → Rotate user-agent from pool                       │
  │  → Remove navigator.webdriver flag                   │
  │  → Random mouse movements (optional)                 │
  │                                                      │
  │  Rate limiting:                                       │
  │  → Token-bucket: 12 tokens/min                       │
  │  → 2-5s jitter between requests                      │
  │  → Exponential backoff on failure                    │
  └──────────────────────────┬────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  SCRAPER CLASSES                                                     │
  │                                                                      │
  │  base_scraper.py (abstract)                                          │
  │       │                                                              │
  │       ├── project_list_scraper.py ──► List page HTML                 │
  │       │   (pagination, project cards)                                │
  │       │                                                              │
  │       ├── project_detail_scraper.py ──► Detail page HTML             │
  │       │   (specs, location, price range)                             │
  │       │                                                              │
  │       └── listing_scraper.py ──► Listing page HTML                   │
  │           (unit listings, ask prices)                                │
  └──────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
  ┌───────────────────────────────────────────────────────┐
  │  PARSING & VALIDATION                                 │
  │  parsers.py + models.py (Pydantic)                    │
  │                                                      │
  │  selectors.py → CSS/XPath selectors                  │
  │  parsers.py   → Raw HTML → structured dict           │
  │  models.py    → Pydantic validation                  │
  │                                                      │
  │  Fields extracted:                                   │
  │  → project_name, slug, location                      │
  │  → price_range (min/max), unit_type                  │
  │  → area_range, floor_count, developer                │
  │  → listing_count, ask_price                          │
  └──────────────────────────┬────────────────────────────┘
                             │
                             ▼
  ┌───────────────────────────────────────────────────────┐
  │  PROJECT MATCHING                                     │
  │  utils/project_matcher.py                            │
  │                                                      │
  │  → Normalize names (lowercase, remove junk words)    │
  │  → Fuzzy match against DB project names              │
  │  → Check project_aliases.json for known variants     │
  │  → Threshold: ≥ 0.85 similarity for auto-match       │
  │  → Below threshold: save to unmatched_projects.json  │
  └──────────────────────────┬────────────────────────────┘
                             │
                             ▼
  ┌───────────────────────────────────────────────────────┐
  │  STAGING TABLE                                        │
  │  scraped_listings (status: pending)                   │
  │                                                      │
  │  → Stores all scraped records with job_id            │
  │  → Links to scrape_jobs table                        │
  │  → Awaits human review and promote decision          │
  └──────────────────────────┬────────────────────────────┘
                             │
              (after review: promote command)
                             │
                             ▼
  ┌───────────────────────────────────────────────────────┐
  │  PROMOTE TO PRODUCTION                                │
  │  pipeline.py promote()                               │
  │                                                      │
  │  → Validate all records in job                       │
  │  → Create price_records for specified period_id      │
  │  → Update scraped_listings status → 'promoted'       │
  │  → Record data_lineage (source: scrape)              │
  └──────────────────────────────────────────────────────┘
```

---

## 5. Database Layer

### Schema Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATABASE SCHEMA (22 TABLES)                           │
└─────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  GEOGRAPHIC HIERARCHY                                                │
  │                                                                      │
  │  cities ──────────► districts ──────────► wards                     │
  │  (id, name,          (id, name,            (id, name,               │
  │   slug, region)       city_id)              district_id)             │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  PROJECT HIERARCHY                                                   │
  │                                                                      │
  │  developers ──► projects ──► project_blocks ──► unit_types           │
  │  (id, name,     (id, name,   (id, name,          (id, type,         │
  │   stock_code,    dev_id,      project_id,          block_id,         │
  │   hq, founded)   district_id, phase, units)        area_min/max,     │
  │                  type,                             bedrooms)         │
  │                  status,                                             │
  │                  bds_slug,                                           │
  │                  bds_url)                                            │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  PRICING                                                             │
  │                                                                      │
  │  report_periods ──► price_records ──► price_change_factors           │
  │  (id, label,        (id, project_id,  (id, price_record_id,         │
  │   year, half)        period_id,        factor_type,                  │
  │                      price_usd,        description,                  │
  │                      price_vnd,        impact_level)                 │
  │                      grade,                                          │
  │                      source_type)                                    │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  SUPPLY & SALES                                                      │
  │                                                                      │
  │  supply_records                    sales_statuses                    │
  │  (id, project_id,                  (id, project_id,                 │
  │   period_id,                        period_id,                       │
  │   total_units,                      launched_units,                  │
  │   available_units,                  sold_units,                      │
  │   absorption_rate)                  available_units)                 │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  ANALYSIS                                                            │
  │                                                                      │
  │  grade_definitions              competitor_comparisons               │
  │  (id, city_id, grade,           (id, project_a_id,                  │
  │   label, price_min_usd,          project_b_id,                       │
  │   price_max_usd)                 dimension, score_a, score_b)        │
  │                                                                      │
  │  market_segment_summaries        district_metrics                    │
  │  (id, city_id, district_id,      (id, district_id,                  │
  │   period_id, segment,             period_id,                         │
  │   total_supply,                   avg_price_usd,                     │
  │   avg_price_usd,                  total_supply,                      │
  │   absorption_rate)                absorption_rate)                   │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  FACILITIES                                                          │
  │                                                                      │
  │  project_facilities              project_sales_points                │
  │  (id, project_id,                (id, project_id,                   │
  │   facility_type,                  message_type,                      │
  │   description)                    content)                           │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  METADATA & LINEAGE                                                  │
  │                                                                      │
  │  source_reports                  data_lineage                        │
  │  (id, filename,                  (id, table_name,                   │
  │   report_type,                    record_id,                         │
  │   city_id,                        source_report_id,                  │
  │   period_id,                      source_type,                       │
  │   pages, quality_score)           extracted_at)                      │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  SCRAPING                                                            │
  │                                                                      │
  │  scrape_jobs ──────────────────► scraped_listings                    │
  │  (id, city_slug,                 (id, job_id,                       │
  │   status, started_at,             project_id (nullable),             │
  │   completed_at,                   project_name_raw,                  │
  │   records_scraped)                price_usd,                         │
  │                                   status: pending/promoted)          │
  └─────────────────────────────────────────────────────────────────────┘
```

### Connection Architecture

```
src/db/connection.py
     │
     ├── create_engine()         # SQLite engine with check_same_thread=False
     │   PRAGMA foreign_keys=ON  # Enforce FK constraints
     │
     └── get_session()           # Context manager (Session factory)
           ├── session.begin()
           ├── yield session
           └── session.commit() / rollback()
```

---

## 6. Analysis & Query Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ANALYSIS & QUERY PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────┘

  USER QUERY (natural language or slash command)
            │
            ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  COMMAND ROUTER                                                      │
  │  .claude/commands/{command}.md                                       │
  │                                                                      │
  │  Parses: city, district, project names, period                       │
  │  Routes to: appropriate agent or report module                       │
  └──────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  QUERY HELPERS                                                       │
  │  src/db/queries.py                                                   │
  │                                                                      │
  │  → resolve_city_name()    # "HCMC" → "Ho Chi Minh City"             │
  │  → get_projects_for_city() # city_id, period filters                │
  │  → get_price_history()    # project → price records                 │
  │  → get_supply_metrics()   # district → supply/absorption            │
  │  → get_district_stats()   # aggregate metrics per district          │
  └──────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  SQLALCHEMY QUERIES                                                  │
  │                                                                      │
  │  Declarative 2.x style:                                              │
  │  session.execute(                                                    │
  │      select(Project)                                                 │
  │      .join(District).join(City)                                      │
  │      .where(City.slug == city_slug)                                  │
  │      .options(selectinload(Project.price_records))                   │
  │  )                                                                   │
  └──────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  REPORT RENDERER                                                     │
  │  src/reports/ + templates/                                           │
  │                                                                      │
  │  Jinja2 template rendering:                                          │
  │  → Load data from DB into context dict                               │
  │  → Render Jinja2 template with context                               │
  │  → Return markdown string                                            │
  └──────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
                    Markdown Report Output
```

---

## 7. Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AGENT ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────┘

  .claude/agents/
  ─────────────

  ┌─────────────────────────────────────────────────────────────────────┐
  │  data-extractor                                                      │
  │  ──────────────                                                      │
  │  Trigger: New PDF text extracted                                     │
  │                                                                      │
  │  Input:   Raw text from user_resources/**/extracted/*.txt            │
  │  Process: Text → JSON → validate against seed schema                 │
  │  Output:  JSON objects ready for seeders                             │
  │                                                                      │
  │  Knowledge:                                                          │
  │  → Grade system (SL/L/H-I/.../A-II per city)                        │
  │  → NHO-PD report structure (passes 1/2/3)                           │
  │  → Seed JSON schemas for all 22 tables                               │
  │  → Vietnamese real estate terminology                                │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  market-analyzer                                                     │
  │  ───────────────                                                     │
  │  Trigger: Slash commands (/vn-market-briefing, /zone-analysis, etc.) │
  │                                                                      │
  │  Input:   City, district, period, project names                      │
  │  Process: NL query → SQLAlchemy → DB → structured response           │
  │  Output:  Markdown with summary, data tables, insights               │
  │                                                                      │
  │  Analysis types:                                                     │
  │  → Market overview (city-level snapshot)                             │
  │  → Price analysis (grade comparisons, period changes)               │
  │  → Supply-demand (absorption rates, pipeline)                       │
  │  → Segment analysis (luxury/mid-end/affordable breakdown)           │
  │  → Developer portfolio (cross-project analysis)                     │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │  competitor-benchmarker                                              │
  │  ──────────────────────                                              │
  │  Trigger: /competitor-compare command                                │
  │                                                                      │
  │  Input:   2–3 project names                                          │
  │  Process: DB lookup → 11-dim scoring → comparison matrix            │
  │  Output:  Scored matrix, strengths/weaknesses, recommendation       │
  │                                                                      │
  │  11 Dimensions:                                                      │
  │  1. Location accessibility    7. Pricing vs value                   │
  │  2. Transportation links      8. Developer brand                    │
  │  3. Surrounding amenities     9. Payment terms                      │
  │  4. Design quality           10. Legal status                       │
  │  5. Internal facilities      11. Property management                │
  │  6. Unit layout efficiency                                           │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Slash Command Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SLASH COMMAND ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

  USER INPUT: /vn-market-briefing HCMC 2024-H1
                         │
                         ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │  COMMAND FILE                                                     │
  │  .claude/commands/vn-market-briefing.md                          │
  │                                                                  │
  │  Contains:                                                       │
  │  → Frontmatter (description, usage, allowed_tools)              │
  │  → Prompt template with {{$ARGUMENTS}} placeholder              │
  │  → Output format specification                                  │
  │  → Data source instructions                                     │
  └──────────────────────────────┬───────────────────────────────────┘
                                 │
                  ┌──────────────┼──────────────────┐
                  │              │                   │
                  ▼              ▼                   ▼
         ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
         │  DB Query    │ │  Agent Call   │ │  Report Module   │
         │  queries.py  │ │  market-      │ │  market_briefing │
         │              │ │  analyzer     │ │  .py             │
         └──────┬───────┘ └──────┬────────┘ └───────┬──────────┘
                │                │                   │
                └────────────────┴───────────────────┘
                                 │
                                 ▼
                      Markdown Report Output


  COMMAND REGISTRY:
  ─────────────────

  /vn-market-briefing  → market_briefing.py   (city overview)
  /project-profile     → project_profile.py   (single project)
  /competitor-compare  → competitor_benchmark.py (11-dim)
  /zone-analysis       → zone_analysis.py     (district)
  /price-check         → price_trends.py      (grade lookup)
  /db-query            → queries.py (direct)  (NL → SQL)
  /land-review         → land_review.py       (feasibility)
```

---

## 9. Report Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    REPORT GENERATION PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐
  │  Report Request  │
  │  (city, project, │
  │   period, etc.)  │
  └────────┬─────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────┐
  │  DATA COLLECTION LAYER                                 │
  │  src/reports/{report_type}.py                         │
  │                                                        │
  │  1. Open DB session                                    │
  │  2. Execute queries via queries.py helpers            │
  │  3. Join related tables (Project+Developer+District)  │
  │  4. Calculate derived metrics:                        │
  │     - Price change % (period over period)             │
  │     - Absorption rate (sold / total available)        │
  │     - Grade position (rank within grade peers)        │
  │     - District supply concentration                   │
  │  5. Collect into context dict                         │
  └────────────────────┬───────────────────────────────────┘
                       │
                       ▼
  ┌────────────────────────────────────────────────────────┐
  │  OPTIONAL: CHART GENERATION                           │
  │  src/reports/charts.py                                │
  │                                                        │
  │  → Price trend line charts (matplotlib)               │
  │  → Grade distribution bar charts                     │
  │  → Supply pipeline charts                            │
  │  → Location maps (Folium, if coordinates available)  │
  └────────────────────┬───────────────────────────────────┘
                       │
                       ▼
  ┌────────────────────────────────────────────────────────┐
  │  TEMPLATE RENDERING                                   │
  │  src/reports/renderer.py + templates/                 │
  │                                                        │
  │  → Load Jinja2 template for report type              │
  │  → Pass context dict to template                     │
  │  → Render to markdown string                         │
  └────────────────────┬───────────────────────────────────┘
                       │
                       ▼
  ┌────────────────────────────────────────────────────────┐
  │  OUTPUT                                               │
  │                                                        │
  │  → Return markdown string (for slash commands)       │
  │  → OR save to output/*.md (for land reviews)         │
  └────────────────────────────────────────────────────────┘
```

---

## 10. Component Dependency Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPONENT DEPENDENCY MAP                              │
└─────────────────────────────────────────────────────────────────────────┘

  src/config.py
      │ (used by all modules for paths and constants)
      │
      ├── src/db/connection.py ──► src/db/models.py
      │        │
      │        └── src/db/queries.py
      │                 │
      │                 ├── src/reports/market_briefing.py
      │                 ├── src/reports/project_profile.py
      │                 ├── src/reports/zone_analysis.py
      │                 ├── src/reports/price_trends.py
      │                 ├── src/reports/competitor_benchmark.py
      │                 ├── src/reports/land_review.py
      │                 └── src/reports/charts.py
      │
      ├── src/seeders/ ──► data/seed/*.json ──► src/db/models.py
      │        │
      │        └── src/seeders/run_all.py (orchestrator)
      │
      ├── src/collectors/ ──► src/extractors/ ──► src/utils/text_parser.py
      │
      ├── src/scrapers/
      │        │
      │        ├── browser.py (Playwright)
      │        ├── rate_limiter.py
      │        ├── base_scraper.py
      │        │       ├── project_list_scraper.py
      │        │       ├── project_detail_scraper.py
      │        │       └── listing_scraper.py
      │        ├── parsers.py ──► selectors.py
      │        ├── models.py (Pydantic)
      │        └── pipeline.py ──► src/utils/project_matcher.py
      │
      └── src/utils/
               ├── project_matcher.py ──► data/seed/project_aliases.json
               ├── geo_utils.py
               ├── infrastructure_scoring.py
               ├── regulatory_data.py
               └── lineage_tracker.py ──► src/db/models.py (DataLineage)


  EXTERNAL DEPENDENCIES:
  ─────────────────────

  Playwright ──► Browser automation (scraping)
  PyMuPDF    ──► PDF text extraction
  SQLAlchemy ──► ORM + query building
  Pydantic   ──► Input validation
  Jinja2     ──► Template rendering
  Folium     ──► Interactive maps
  Matplotlib ──► Chart generation
```

---

## 11. Module Reference

### src/ Directory Layout

```
src/
├── config.py                    # PROJECT_ROOT, DB_PATH, constants
│
├── db/
│   ├── connection.py            # Engine + Session factory
│   ├── models.py                # 22 SQLAlchemy Mapped models
│   ├── init_db.py               # CREATE TABLE + idempotent migrations
│   └── queries.py               # Reusable query helpers
│
├── seeders/
│   ├── base_seeder.py           # Abstract seeder (_get_or_create)
│   ├── city_seeder.py           # Reference: cities
│   ├── district_seeder.py       # Reference: districts
│   ├── grade_seeder.py          # Grade definitions by city
│   ├── developer_seeder.py      # Developer companies
│   ├── project_seeder.py        # Projects (core entity)
│   ├── block_seeder.py          # Project blocks/phases
│   ├── unit_type_seeder.py      # Unit type configurations
│   ├── price_seeder.py          # Price records by period
│   ├── price_factor_seeder.py   # Price change factors
│   ├── supply_seeder.py         # Supply/absorption metrics
│   ├── sales_status_seeder.py   # Sales status per period
│   ├── facility_seeder.py       # Project facilities
│   ├── sales_point_seeder.py    # Marketing messages
│   ├── competitor_seeder.py     # Competitor comparisons
│   ├── market_segment_seeder.py # Segment summaries
│   ├── district_metric_seeder.py# District-level KPIs
│   ├── source_report_seeder.py  # Source PDF metadata
│   └── run_all.py               # Dependency-ordered orchestrator
│
├── extractors/
│   ├── base_extractor.py        # Abstract extractor
│   ├── market_pass_extractor.py # Market/project data from PDFs
│   ├── price_pass_extractor.py  # Price table extraction
│   ├── casestudy_extractor.py   # Case study project data
│   ├── land_review_extractor.py # Land feasibility data
│   └── run_all.py               # Run all extractors
│
├── collectors/
│   ├── orchestrator.py          # Main ingestion orchestrator
│   ├── pdf_metadata.py          # PDF quality/metadata extraction
│   ├── pdf_extractor.py         # PyMuPDF text extraction
│   ├── watcher.py               # File system watcher
│   ├── cli_ingest_pdf.py        # CLI: single PDF
│   ├── cli_scan_folder.py       # CLI: batch folder
│   ├── cli_watch.py             # CLI: start watcher
│   ├── cli_status.py            # CLI: ingestion status
│   └── cli_utils.py             # Formatting helpers
│
├── scrapers/
│   ├── config.py                # URLs, slugs, rate limits
│   ├── browser.py               # Playwright + anti-detection
│   ├── rate_limiter.py          # Token-bucket rate limiter
│   ├── base_scraper.py          # Abstract + retry logic
│   ├── project_list_scraper.py  # BDS project list pages
│   ├── project_detail_scraper.py# BDS project detail pages
│   ├── listing_scraper.py       # BDS listing pages
│   ├── selectors.py             # CSS/XPath selectors
│   ├── parsers.py               # HTML → structured dict
│   ├── models.py                # Pydantic validation models
│   ├── pipeline.py              # Full scrape pipeline
│   ├── cli_scrape.py            # CLI entry point
│   └── __main__.py              # Module entry point
│
├── reports/
│   ├── renderer.py              # Jinja2 renderer
│   ├── market_briefing.py       # City market overview
│   ├── project_profile.py       # Single project report
│   ├── zone_analysis.py         # District analysis
│   ├── price_trends.py          # Price movement analysis
│   ├── segment_analysis.py      # Segment comparisons
│   ├── competitor_benchmark.py  # 11-dimension scoring
│   ├── district_dashboard.py    # District KPI dashboard
│   ├── land_review.py           # Land feasibility report
│   ├── data_lineage.py          # Data provenance report
│   ├── location_map.py          # Folium map generation
│   └── charts.py                # Matplotlib/Plotly charts
│
└── utils/
    ├── text_parser.py           # PDF text + table parsing
    ├── project_matcher.py       # Fuzzy project name matching
    ├── geo_utils.py             # Distance, area, coordinates
    ├── infrastructure_scoring.py# Infrastructure quality scores
    ├── regulatory_data.py       # Regulatory constraints by district
    ├── lineage_tracker.py       # Data lineage tracking
    └── match_diagnostic.py      # Matching problem diagnostics
```

---

## Key Design Principles

1. **Idempotency**: All seeders and migrations are safe to run multiple times.
2. **Staging before production**: Scraped data goes to `scraped_listings` before promotion to `price_records`.
3. **Data lineage**: Every record tracks its source (PDF, scrape, manual, derived).
4. **Grade-relative analysis**: All price comparisons are grade-normalized (compare within grade tiers).
5. **City-specific grades**: Grade thresholds differ between cities — HCMC ≠ Binh Duong grades.
6. **Foreign key enforcement**: SQLite `PRAGMA foreign_keys=ON` enforced on every connection.
7. **In-memory tests**: Tests use `sqlite:///:memory:` for isolation from production data.
