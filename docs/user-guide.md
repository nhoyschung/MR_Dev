# MR-System User Guide
**Vietnam Real Estate Market Research System**

> Version: Sprint 9 | Updated: 2026-02

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [Core Concepts](#3-core-concepts)
4. [Database Management](#4-database-management)
5. [Data Ingestion — PDF Reports](#5-data-ingestion--pdf-reports)
6. [Web Scraping — BDS.com.vn](#6-web-scraping--bdscomvn)
7. [Analysis with Slash Commands](#7-analysis-with-slash-commands)
8. [AI Agent System](#8-ai-agent-system)
9. [Report Generation](#9-report-generation)
10. [Land Review System](#10-land-review-system)
11. [CLI Reference](#11-cli-reference)
12. [Testing](#12-testing)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Overview

MR-System is a Vietnam real estate market intelligence platform built to process NHO-PD analysis reports and BDS.com.vn web data. It provides structured market data storage, automated extraction, and AI-powered analysis through Claude Code agents and slash commands.

**Key capabilities:**
- Ingest and parse NHO-PD PDF reports (1,200+ pages across 11 reports)
- Scrape live project and pricing data from BDS.com.vn
- Store structured market data in SQLite (22 tables, 227+ seed records)
- Generate market briefings, project profiles, competitor comparisons, zone analyses
- Conduct land feasibility reviews with infrastructure and regulatory scoring

**Supported markets:**
| City | Slug | Coverage |
|------|------|----------|
| Ho Chi Minh City | tp-hcm | Full — all districts |
| Hanoi | ha-noi | Full — all districts |
| Binh Duong | binh-duong | Partial — key districts |
| Da Nang | da-nang | Partial |

---

## 2. Quick Start

### Prerequisites

```bash
# Python 3.12+, pip
python --version   # should be 3.12+
```

### Installation

```bash
# Clone repository and install dependencies
pip install -r requirements.txt

# Initialize database (creates 22 tables)
python -m src.db.init_db

# Seed all reference and market data
python -m src.seeders.run_all
```

### Verify Installation

```bash
# Run test suite
pytest tests/ -v

# Check database
python -m src.scrapers.cli_scrape status
```

### First Analysis

Once installed, open Claude Code and run:

```
/vn-market-briefing HCMC 2024-H1
```

---

## 3. Core Concepts

### Grade System

Projects are classified into 8–9 tiers per city:

| Grade | Label | Typical Price (USD/m²) |
|-------|-------|------------------------|
| SL | Super Luxury | > 10,000 |
| L | Luxury | 5,000 – 10,000 |
| H-I | High-end I | 3,000 – 5,000 |
| H-II | High-end II | 2,000 – 3,000 |
| M-I | Mid-end I | 1,500 – 2,000 |
| M-II | Mid-end II | 1,000 – 1,500 |
| M-III | Mid-end III | 700 – 1,000 |
| A-I | Affordable I | 500 – 700 |
| A-II | Affordable II | < 500 |

> Grade ranges vary by city. HCMC grades are higher than Binh Duong equivalents.

### Report Periods

Periods use half-year notation: `YYYY-H1` or `YYYY-H2`.

Examples: `2023-H1`, `2023-H2`, `2024-H1`, `2024-H2`

### Data Lineage

Every data record tracks its source:
- Source type: `pdf`, `scrape`, `manual`, `derived`
- Source file: path to the originating PDF or URL
- Extraction timestamp and confidence score

---

## 4. Database Management

### Schema Overview

The SQLite database at `data/mr_system.db` contains 22 tables:

```
Geographic:    cities → districts → wards
Projects:      developers → projects → project_blocks → unit_types
Pricing:       report_periods → price_records → price_change_factors
Supply:        supply_records → sales_statuses
Analysis:      competitor_comparisons → market_segment_summaries
Grades:        grade_definitions
Facilities:    project_facilities → project_sales_points
Metadata:      source_reports → data_lineage → district_metrics
Scraping:      scrape_jobs → scraped_listings
```

### Initialize Database

```bash
# Create all tables (idempotent — safe to run repeatedly)
python -m src.db.init_db
```

### Seed Data

```bash
# Seed all tables in dependency order
python -m src.seeders.run_all

# Individual seeders (if needed)
python -m src.seeders.city_seeder
python -m src.seeders.developer_seeder
python -m src.seeders.project_seeder
```

Seed files are located in `data/seed/*.json`. Seeders use `_get_or_create()` for idempotency — running twice does not duplicate records.

### Direct SQL Access

```bash
# Open SQLite shell
sqlite3 data/mr_system.db

# Useful queries
.tables
SELECT COUNT(*) FROM projects;
SELECT name, city_id FROM projects LIMIT 10;
```

---

## 5. Data Ingestion — PDF Reports

The PDF collection system processes NHO-PD market reports and extracts structured data.

### Workflow

```
PDF File → Extract Text → Parse Sections → Validate → Seed to DB
```

### Single PDF Ingestion

```bash
python -m src.collectors.cli_ingest_pdf path/to/report.pdf
```

### Batch Folder Scan

```bash
# Scan a folder for all PDFs and ingest
python -m src.collectors.cli_scan_folder user_resources/D_colect/

# Options
--dry-run        # Preview without inserting
--force          # Re-process already-ingested files
```

### Real-time File Watcher

```bash
# Watch a directory for new PDFs (runs continuously)
python -m src.collectors.cli_watch user_resources/D_colect/
```

The watcher automatically detects new `.pdf` files and triggers ingestion. Useful for drop-folder workflows.

### Ingestion Status

```bash
# Show ingestion statistics and recent jobs
python -m src.collectors.cli_status

# Filter by city
python -m src.collectors.cli_status --city HCMC
```

### Extraction Pipeline

Extractors in `src/extractors/` parse different sections of NHO-PD reports:

| Extractor | Purpose |
|-----------|---------|
| `market_pass_extractor.py` | Market overview, project inventory |
| `price_pass_extractor.py` | Price tables, grade pricing |
| `casestudy_extractor.py` | Case study project data |
| `land_review_extractor.py` | Land feasibility analysis |

Run all extractors:

```bash
python -m src.extractors.run_all
```

---

## 6. Web Scraping — BDS.com.vn

The scraper collects live project listings and pricing from BDS.com.vn using Playwright.

### Scraping Pipeline

```
BDS Website → Playwright Browser → Parse HTML → Validate (Pydantic) → Match Projects → Stage → Promote
```

### Available Commands

```bash
# Scrape project list for a city
python -m src.scrapers.cli_scrape projects --city hcmc

# Scrape listings for a specific project
python -m src.scrapers.cli_scrape listings --project vinhomes-grand-park

# Show job history and statistics
python -m src.scrapers.cli_scrape status

# Promote staged listings to price_records
python -m src.scrapers.cli_scrape promote --job-id 5 --period-id 3
```

### City Slugs

| City | Slug |
|------|------|
| HCMC | tp-hcm |
| Hanoi | ha-noi |
| Binh Duong | binh-duong |
| Da Nang | da-nang |

### Rate Limiting

The scraper uses a token-bucket rate limiter:
- **Max rate**: 12 requests per minute
- **Delay**: 2–5 seconds with random jitter
- **Retries**: Exponential backoff (3 attempts)
- **Anti-detection**: Rotating user-agents, viewport randomization, webdriver flag removal

### Staging → Promote Workflow

Scraped listings go to `scraped_listings` (staging) first:

1. **Scrape** → data enters `scraped_listings` with `status = 'pending'`
2. **Review** → check staging data for quality
3. **Promote** → convert staging records to `price_records` for the specified period

```bash
# Review staging data
python -m src.scrapers.cli_scrape status

# Promote after review
python -m src.scrapers.cli_scrape promote --job-id 5 --period-id 3
```

### Project Matching

The `ProjectMatcher` in `src/utils/project_matcher.py` fuzzy-matches scraped project names to database IDs. Unmatched projects are saved to `data/seed/unmatched_projects.json` for manual review.

```bash
# Show remaining unmatched projects
python scripts/show_remaining_unmatched.py
```

---

## 7. Analysis with Slash Commands

In Claude Code, use these slash commands for market analysis. All commands query the live database.

### `/vn-market-briefing`

**Market overview for a city and period.**

```
/vn-market-briefing HCMC 2024-H1
/vn-market-briefing Hanoi 2024-H2
/vn-market-briefing Binh Duong 2024-H1
```

Output sections:
- Market snapshot (total projects, units, average price)
- Grade distribution (SL → A-II breakdown)
- Top districts by supply and absorption
- Price trends (period over period)
- Supply pipeline (upcoming launches)
- Key market takeaways

### `/project-profile`

**Deep dive on a single project.**

```
/project-profile Vinhomes Grand Park
/project-profile The Matrix One
/project-profile Masteri Waterfront
```

Output sections:
- Project identity (developer, location, status, type)
- Pricing (primary + secondary market, price per m², grade)
- Developer context (portfolio, reputation)
- Location context (district supply-demand, infrastructure)
- Competitive positioning (grade peers, price ranking)
- Sales status (absorption rate, available units)

### `/competitor-compare`

**Side-by-side comparison of 2–3 projects.**

```
/competitor-compare Vinhomes Grand Park vs Masteri Centre Point
/competitor-compare The Matrix One vs Sky Oasis vs Sunshine City
```

Dimensions scored 1–10:
1. Location accessibility
2. Transportation links
3. Surrounding amenities
4. Design quality
5. Internal facilities
6. Unit layout efficiency
7. Pricing vs value
8. Developer brand
9. Payment terms flexibility
10. Legal status
11. Property management quality

### `/zone-analysis`

**District-level supply and demand analysis.**

```
/zone-analysis Thu Duc HCMC
/zone-analysis Cau Giay Hanoi
/zone-analysis Di An Binh Duong
```

Output sections:
- Zone overview (total supply, active projects, average price)
- Supply pipeline by grade and type
- Price landscape (price range, grade distribution)
- Project roster (active projects in district)
- Absorption and demand metrics
- Investment outlook and risks

### `/price-check`

**Price lookup with grade context.**

```
/price-check Vinhomes Grand Park
/price-check 3500 HCMC
/price-check Sunshine City Hanoi
```

Output:
- Current price (USD/m² and VND/m²)
- Grade classification
- Grade price range and position within grade
- Grade peers (similar projects)
- Price change history

### `/db-query`

**Natural language database queries.**

```
/db-query How many projects in each city?
/db-query Average price by district in HCMC for 2024-H2
/db-query Top 10 projects by absorption rate
/db-query Projects launched after 2023 in Hanoi
```

The agent translates natural language to SQLAlchemy queries and returns formatted markdown tables.

### `/land-review`

**Land development feasibility analysis.**

```
/land-review
city: HCMC
district: Thu Duc
area_ha: 5.2
coordinates: 10.8231, 106.6297
```

Output sections:
- Land overview and zoning
- Infrastructure scoring (roads, utilities, schools, hospitals)
- Regulatory constraints and requirements
- Market context (comparable projects, demand)
- Financial feasibility indicators
- Risk factors

---

## 8. AI Agent System

Three specialized Claude sub-agents handle complex analysis tasks. Agents are invoked automatically by slash commands or can be called directly.

### data-extractor

**Purpose**: Extracts structured JSON from NHO-PD PDF text.

**When to use**: After extracting text from a new PDF report, use this agent to convert raw text into seed-compatible JSON.

**Input**: Text extracted from NHO-PD reports (in `user_resources/D_colect/extracted/`)

**Output**: JSON objects matching seed schemas (`projects`, `prices`, `supply`, `facilities`, etc.)

**Invocation**: Claude Code automatically uses this agent during PDF ingestion. For manual use:

```
Use the data-extractor agent to parse this PDF text: [paste extracted text]
```

### market-analyzer

**Purpose**: Queries the database for market insights.

**Analysis types**:
- Market overview (snapshot, trends)
- Price analysis (grade comparisons, period changes)
- Supply-demand metrics
- Segment analysis (luxury vs mid-end vs affordable)
- Developer portfolio analysis

**Output format**: Structured with summary → data tables → insights → data source citation.

**Invocation**: Used by `/vn-market-briefing`, `/zone-analysis`, `/price-check`.

### competitor-benchmarker

**Purpose**: Performs the 11-dimension competitive scoring.

**Scoring methodology**:
- Each dimension scored 1–10
- Weighted average produces overall score
- Relative strengths and weaknesses identified

**Invocation**: Used by `/competitor-compare`. Direct invocation:

```
Use the competitor-benchmarker to compare Vinhomes Grand Park and Masteri Centre Point
```

---

## 9. Report Generation

Reports are generated programmatically from database data using Jinja2 templates.

### Available Report Modules

| Module | File | Description |
|--------|------|-------------|
| Market Briefing | `src/reports/market_briefing.py` | City market overview |
| Project Profile | `src/reports/project_profile.py` | Single project deep dive |
| Zone Analysis | `src/reports/zone_analysis.py` | District analysis |
| Price Trends | `src/reports/price_trends.py` | Price movement analysis |
| Segment Analysis | `src/reports/segment_analysis.py` | Segment comparisons |
| Competitor Benchmark | `src/reports/competitor_benchmark.py` | 11-dim scoring |
| District Dashboard | `src/reports/district_dashboard.py` | KPI dashboard |
| Land Review | `src/reports/land_review.py` | Feasibility analysis |
| Data Lineage | `src/reports/data_lineage.py` | Source provenance |

### Python API

```python
from src.db.connection import get_session
from src.reports.market_briefing import render_market_briefing

with get_session() as session:
    report = render_market_briefing(session, city="HCMC", period="2024-H1")
    print(report)
```

### Output Directory

Generated reports are saved to `output/`. Example output file:

```
output/land_review_binh_duong_thuan_an_45ha.md
```

---

## 10. Land Review System

The land review system provides feasibility analysis for potential development sites.

### Input Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `city` | Target city | HCMC, Hanoi, Binh Duong |
| `district` | District name | Thu Duc, Cau Giay, Di An |
| `area_ha` | Site area in hectares | 5.2 |
| `coordinates` | Lat/lon of site center | 10.8231, 106.6297 |
| `zoning` | Current zoning type | residential, mixed-use |
| `frontage_m` | Road frontage in meters | 50 |

### Scoring Dimensions

**Infrastructure Score** (0–100):
- Road access and connectivity
- Utility availability (water, power, sewage)
- School and education proximity
- Healthcare facility proximity
- Public transit access

**Regulatory Score** (0–100):
- Zoning compatibility
- Setback requirements
- Height restrictions
- Environmental constraints
- Legal status of land

**Market Score** (0–100):
- Comparable project pricing
- Demand indicators
- Supply pipeline competition
- Absorption rates in district

### Output Includes

- Executive summary with overall feasibility rating
- Infrastructure scoring breakdown
- Regulatory constraints and compliance checklist
- Market context with comparable projects
- Financial feasibility indicators (estimated sellable area, revenue range)
- Risk matrix
- Recommendations

---

## 11. CLI Reference

### Database Commands

```bash
python -m src.db.init_db                     # Initialize/migrate database
python -m src.seeders.run_all                # Seed all data
```

### PDF Collection Commands

```bash
python -m src.collectors.cli_ingest_pdf <path>    # Ingest single PDF
python -m src.collectors.cli_scan_folder <dir>    # Batch scan folder
python -m src.collectors.cli_watch <dir>          # Start file watcher
python -m src.collectors.cli_status               # Show ingestion status
```

### Scraper Commands

```bash
python -m src.scrapers.cli_scrape projects --city hcmc          # Scrape projects
python -m src.scrapers.cli_scrape listings --project <slug>     # Scrape listings
python -m src.scrapers.cli_scrape status                        # Show job history
python -m src.scrapers.cli_scrape promote --job-id N --period-id N  # Promote to DB
```

### Extractor Commands

```bash
python -m src.extractors.run_all             # Run all extractors
```

### Utility Scripts

```bash
python scripts/show_remaining_unmatched.py   # Show unmatched scraped projects
python scripts/enrich_from_scraped.py        # Enrich projects from scraped data
python scripts/migrate_scraper_tables.py     # Migrate scraper schema
```

### Test Commands

```bash
pytest tests/ -v                             # All tests
pytest tests/test_models.py -v               # Model tests only
pytest tests/test_scrapers.py -v             # Scraper tests only
pytest tests/ -k "project_matcher" -v        # Specific test filter
```

---

## 12. Testing

All tests use in-memory SQLite (`sqlite:///:memory:`) for isolation.

### Test Files

| File | Coverage |
|------|----------|
| `test_models.py` | SQLAlchemy models, relationships, constraints |
| `test_queries.py` | Query helpers, city lookups, aggregations |
| `test_seeders.py` | Seeder idempotency, validation |
| `test_new_seeders.py` | District metrics, source reports, competitor seeders |
| `test_extractors.py` | Text extraction, JSON parsing |
| `test_land_review_extractor.py` | Land review extraction |
| `test_project_matcher.py` | Fuzzy project name matching |
| `test_reports.py` | Report rendering, data aggregation |
| `test_scrapers.py` | Web scraper parsing, browser, rate limiter |
| `test_geo_utils.py` | Geospatial calculations |
| `test_watcher.py` | File watcher detection |

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Specific test file
pytest tests/test_models.py -v

# Pattern match
pytest -k "price" -v
```

---

## 13. Troubleshooting

### Database Issues

**"no such table" error**
```bash
python -m src.db.init_db   # Re-run initialization
```

**Missing columns (bds_slug, bds_url, district_id)**
```bash
python -m src.db.init_db   # Migration runs automatically
```

**Duplicate key errors in seeders**
Seeders use `_get_or_create()`. If duplicates occur, check that the seed JSON has unique identifiers.

### Scraper Issues

**Playwright browser not found**
```bash
pip install playwright
playwright install chromium
```

**Rate limit exceeded / IP blocked**
The scraper automatically backs off. If blocked, wait 30 minutes before retrying.

**Project not matching**
Check `data/seed/unmatched_projects.json` and add aliases to `data/seed/project_aliases.json`.

### PDF Ingestion Issues

**PDF extraction returns empty text**
Some PDFs are image-based. The system uses PyMuPDF for text extraction — image PDFs require OCR which is not currently supported.

**Low confidence scores**
Check the source PDF quality. NHO-PD reports should have confidence > 0.7.

### Slash Command Issues

**"No data found" in commands**
Ensure the database is seeded:
```bash
python -m src.seeders.run_all
```

**Command returns outdated data**
Scrape fresh data:
```bash
python -m src.scrapers.cli_scrape projects --city hcmc
```

---

## Appendix: Key File Paths

| Resource | Path |
|----------|------|
| Database | `data/mr_system.db` |
| Seed data | `data/seed/*.json` |
| Source PDFs | `user_resources/D_colect/` |
| Extracted text | `user_resources/D_colect/extracted/` |
| Report output | `output/` |
| Templates | `templates/` |
| Config | `src/config.py` |
| Models | `src/db/models.py` |
| Agents | `.claude/agents/` |
| Commands | `.claude/commands/` |
