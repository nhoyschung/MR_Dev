# MR-System Improvement Proposals
**Comprehensive System Enhancement Roadmap**

> Analyzed: 2026-02 | Scope: Data Model · Scraping · Analysis · Reporting · Agents · UX

---

## Executive Summary

The MR-System has a solid architectural foundation — 22-table schema, idempotent seeders, staged scraping pipeline, and a functional agent+command layer. However, the current system is **reactive and descriptive**: it stores and retrieves market data well, but lacks depth in predictive analytics, risk assessment, competitive intelligence, and data quality control.

The 5 highest-leverage improvements are:

1. **Temporal trend queries + price forecasting** — system cannot forecast future prices
2. **Data reconciliation** — BDS scrape vs. NHO-PD data conflicts are undetected
3. **Macro context integration** — market briefings lack interest rates, GDP, regulatory signals
4. **Developer scorecard** — developer quality is unscored despite being a key investment signal
5. **Interactive output** — static Markdown reports limit distribution and usability

---

## Improvement Areas

### 1. Data Model

#### 1.1 Missing Columns — High Priority

**`projects` table:**
```
year_built               INTEGER       -- construction completion year
ownership_structure      TEXT          -- public / private / joint-venture / foreign
sustainability_cert      TEXT          -- LEED / EDGE / LOTUS (Green Building)
size_classification      TEXT          -- small (<5k units) / medium / large
phase_count              INTEGER       -- number of development phases
```

**`price_records` table:**
```
price_trend              TEXT          -- up / down / stable (period over period)
days_on_market           INTEGER       -- average listing age from BDS
discount_pct             REAL          -- launch price vs. actual transacted price
data_freshness           TEXT          -- current / recent / stale / very_stale
```

**`supply_records` table:**
```
units_by_bedroom         JSON          -- {"1BR": 120, "2BR": 340, "3BR": 80}
monthly_absorption_rate  REAL          -- period rate / 6
inventory_aging_months   REAL          -- avg months unsold inventory has been listed
```

**`developers` table:**
```
completed_projects_count INTEGER
avg_completion_rate_pct  REAL          -- on-time delivery %
customer_rating          REAL          -- 0-5 from review aggregation
credit_rating            TEXT          -- A+ / A / B+ / B / C (internal assessment)
financial_health_note    TEXT          -- any known distress signals
```

#### 1.2 Missing Tables — Medium Priority

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `macro_indicators` | GDP, interest rates, FDI by period | `period_id`, `indicator_type`, `value`, `source` |
| `regulatory_events` | Zoning changes, tax policy, law updates | `effective_date`, `district_id`, `impact_level`, `description` |
| `project_financing` | Payment plans, bank partner terms | `project_id`, `payment_schedule`, `loan_support_pct` |
| `data_quality_flags` | Flag incomplete/suspicious records | `table_name`, `record_id`, `flag_type`, `severity` |
| `market_alerts` | Threshold-triggered market signals | `alert_type`, `threshold`, `triggered_at`, `resolved_at` |
| `price_forecasts` | Model-generated price predictions | `project_id`, `period_id`, `forecast_usd`, `confidence_interval` |

#### 1.3 Enum Gaps

```python
# Add to config.py
PROJECT_STATUSES_EXTENDED = [
    "pre-launch", "pre-sale", "soft-opening",
    "launched", "selling", "wind-down", "completed", "abandoned"
]

PROJECT_TYPES_EXTENDED = [
    "apartment", "townhouse", "villa", "mixed-use",
    "serviced-apartment", "condotel", "officetel", "commercial"
]

DATA_FRESHNESS = ["current", "recent", "stale", "very_stale"]
MARKET_HEALTH = ["severe_shortage", "shortage", "balanced", "oversupply", "severe_oversupply"]
```

---

### 2. Query Layer

#### 2.1 Temporal & Trend Queries (Missing Entirely)

```python
# src/db/queries.py — add these

def get_price_momentum(session, city_id, periods=4):
    """Price acceleration: is the rate of change itself increasing?"""

def get_grade_migration_cohort(session, city_id):
    """Projects that moved between grade tiers across periods."""

def get_supply_demand_ratio_by_period(session, city_id):
    """Supply pipeline vs. absorption velocity per period."""

def get_price_volatility_by_grade(session, city_id):
    """Standard deviation of prices within each grade tier."""

def get_district_ranking_change(session, city_id, period_a, period_b):
    """How districts' relative rankings shifted between two periods."""
```

#### 2.2 Competitive Intelligence Queries

```python
def get_competitive_set_by_location(session, project_id, radius_km=3.0):
    """All projects within radius, sorted by grade proximity."""

def get_market_share_by_developer(session, city_id, period_id):
    """% of total units by developer. Returns ranked list."""

def get_developer_price_premium(session, developer_id):
    """Avg % above/below grade median across all developer projects."""

def get_emerging_market_districts(session, city_id, window_periods=2):
    """Districts with above-trend price growth in recent periods."""
```

#### 2.3 Supply Chain & Forecasting

```python
def get_supply_pipeline_by_year(session, city_id):
    """Units expected to enter market per year from planned projects."""

def get_absorption_forecast(session, district_id, periods_ahead=2):
    """Simple trend extrapolation of absorption rate."""

def get_holding_period_roi(session, project_id, entry_period_id):
    """Estimated ROI given entry price, current price, carry costs."""
```

---

### 3. Scraping Pipeline

#### 3.1 Data Reconciliation (Critical)

The current pipeline has no conflict resolution when BDS scrape prices diverge from NHO-PD report data. This needs to be addressed:

```
When promoting scraped data:
  IF price_record already exists for (project_id, period_id):
    IF |BDS_price - NHO_price| / NHO_price > 0.15:  (>15% divergence)
      → Flag as CONFLICT, do not overwrite
      → Create data_quality_flag record
      → Log for human review
    ELSE:
      → Average or prefer higher-confidence source
```

**New status in `scraped_listings`:**
```
pending → matched → promoted
pending → matched → conflict_flagged  ← NEW
pending → unmatched → manual_review   ← NEW
```

#### 3.2 Anomaly Detection

```python
# Add to pipeline.py
def detect_price_anomalies(listings: list[ScrapedListing], grade_stats: dict) -> list:
    """
    Flag listings where price is outside 2.5 sigma of grade mean.
    Returns list of flagged listing IDs.
    """
    mean = grade_stats["mean_usd"]
    std  = grade_stats["std_usd"]
    return [l for l in listings if abs(l.price_usd - mean) > 2.5 * std]
```

#### 3.3 Data Freshness Tracking

```python
# In price_records, add:
scraped_at       = Column(DateTime)   # when BDS listed this price
data_freshness   = Column(String)     # computed: current/recent/stale/very_stale

# Freshness logic:
# current     = scraped within 30 days
# recent      = 30-90 days
# stale       = 90-180 days
# very_stale  = 180+ days
```

#### 3.4 Enhanced ScrapeJob Tracking

```python
# Extend scrape_jobs table:
retry_count          INTEGER   DEFAULT 0
last_error_message   TEXT
pages_attempted      INTEGER
pages_succeeded      INTEGER
coverage_pct         REAL      -- % of target projects with fresh data
```

---

### 4. Analysis & Reporting

#### 4.1 Market Briefing — Missing Sections

Add to `/vn-market-briefing` output:

```markdown
## 7. Macro Context
- GDP growth: X.X% (Q3 2024) — real estate correlation score: high
- Lending rates: XX% (State Bank of Vietnam) — affordability impact: medium
- CPI: X.X% — real price growth after inflation

## 8. Regulatory Signals
- [Date]: [District] rezoned from residential to mixed-use → impacts supply pipeline
- Foreign ownership quota: still 30% cap on condotels (unchanged)

## 9. Risk Factors
- Oversupply warning: Thu Duc has 18-month inventory at current absorption
- Developer credit risk: 2 developers in [city] with public bond delays
- Interest rate sensitivity: 80% of buyers use mortgage financing

## 10. Investment Thesis (2-sentence summary)
```

#### 4.2 Price Forecasting Module

```python
# New file: src/reports/price_forecast.py

from statsmodels.tsa.holtwinters import ExponentialSmoothing
# OR: from prophet import Prophet

def forecast_price_trend(price_history: list[float], periods_ahead: int = 2):
    """
    Generate price forecast using exponential smoothing.
    Returns: (forecast_values, lower_bound, upper_bound) at 95% CI
    """
```

New slash command: `/price-forecast [city] [district] [grade]`

#### 4.3 Developer Scorecard Module

```python
# New file: src/reports/developer_scorecard.py

DEVELOPER_DIMENSIONS = [
    "project_count",          # portfolio size
    "completion_rate_pct",    # on-time delivery
    "price_performance_pct",  # actual vs. advertised price
    "unit_quality_rating",    # customer reviews
    "brand_premium_pct",      # above/below grade median
    "geographic_diversity",   # single-market vs. national
    "market_share_pct",       # % of city supply
    "financial_stability",    # credit rating
]
```

New slash command: `/developer-scorecard [developer name]`

#### 4.4 Output Formats

Currently: Markdown only.

| Format | Use Case | Implementation |
|--------|---------|---------------|
| **HTML** | Web display, email distribution | Jinja2 template → HTML |
| **PDF** | Formal reports, client delivery | `weasyprint` library |
| **Excel** | Analyst data export | `openpyxl` library |
| **JSON** | API integration, downstream tools | Pydantic `.model_dump()` |
| **Interactive HTML** | Dashboard-style reports | Plotly + Jinja2 |

---

### 5. Slash Commands — Missing Commands

#### Tier 1 (High value, relatively simple)

| Command | Purpose | Data Source |
|---------|---------|-------------|
| `/developer-scorecard [name]` | Multi-dimension developer rating | DB: projects + prices + supply |
| `/price-forecast [city] [period]` | 2-period price projection | DB: price_records (time series) |
| `/supply-pipeline [city]` | Units entering market by year | DB: projects + supply_records |
| `/segment-gap [city]` | Identify under-served market segments | DB: grade_definitions + supply |

#### Tier 2 (Medium complexity)

| Command | Purpose |
|---------|---------|
| `/investment-screen [budget] [city]` | Projects matching budget + risk profile |
| `/emerging-districts [city]` | Districts with above-trend momentum |
| `/developer-compare [dev1] vs [dev2]` | Side-by-side developer scorecard |
| `/land-screen [district] [area_ha]` | Quick land feasibility (1-page) vs full `/land-review` |

#### Tier 3 (Requires new data sources)

| Command | Purpose | Requires |
|---------|---------|---------|
| `/market-sentiment [city]` | News + analyst sentiment index | RSS/news API |
| `/regulatory-watch [district]` | Upcoming zoning + policy changes | Regulatory DB |
| `/buyer-affordability [segment]` | Income required vs. population qualified | Census data |
| `/foreign-investment [city]` | Nationality breakdown, FDI trends | CBRE/JLL data |

---

### 6. Agent Enhancements

#### 6.1 market-analyzer Agent

**Add analytical capabilities:**

```markdown
## Scenario Analysis
When asked "what if X happens", the agent should:
1. Identify the relevant variables (supply, demand, price, absorption)
2. Apply the hypothetical change
3. Propagate effects through market model
4. Report impact on grade pricing and absorption
Example: "What if interest rates rise 2%?"
→ Affordability reduces 15-20%, absorption drops from 68% → 55%
→ Price pressure on M-I/M-II grades (most mortgage-dependent)
→ SL/L grades relatively insulated (cash buyers)

## Confidence Levels
Every analytical output should state:
- Data completeness: X/Y fields populated
- Historical depth: N periods of data
- Confidence: High / Medium / Low
- Caveat: [if data is sparse or old]
```

#### 6.2 New Agent: risk-scorer

```markdown
# .claude/agents/risk-scorer.md

Purpose: Score and explain investment risks for projects, districts, or developers.

Risk Dimensions:
1. Market risk (oversupply, price correction)
2. Developer risk (execution, financial health)
3. Legal/regulatory risk (land title, zoning)
4. Macro risk (interest rates, FX, economy)
5. Liquidity risk (how easily can investor exit?)

Output: Risk score (0-100) + breakdown by dimension + key risk factors
```

#### 6.3 New Agent: data-quality-reviewer

```markdown
# .claude/agents/data-quality-reviewer.md

Purpose: Review DB data completeness and flag issues before analysis.

Checks:
- Projects missing price_records for recent period
- Price records with suspicious values (>3 sigma from grade mean)
- Projects with no supply_records
- Unmatched scraped listings (unmatched_projects.json)
- Data freshness (records older than 6 months)

Output: Data quality report with completeness score and priority fixes
```

---

### 7. Infrastructure & Libraries

#### 7.1 Recommended Library Additions

```
# requirements.txt additions

# Analytics
numpy>=1.26
pandas>=2.0
scipy>=1.11

# Forecasting
statsmodels>=0.14      # ARIMA, exponential smoothing

# Visualization
plotly>=5.18           # interactive charts
folium>=0.15           # geographic maps (already partially used)

# Geospatial
shapely>=2.0           # geometric operations (radius queries)
geopy>=2.3             # distance calculations

# Export
openpyxl>=3.1          # Excel export
weasyprint>=60.0       # PDF export from HTML

# Config
python-dotenv>=1.0     # environment variables

# Code quality
pytest-cov>=4.1        # coverage
ruff>=0.1              # linting
```

#### 7.2 Configuration Improvements

```python
# src/config.py — add these constants

# Analysis thresholds
PRICE_ANOMALY_SIGMA = 2.5
ABSORPTION_HEALTHY_MIN_PCT = 60.0
SUPPLY_SHORTAGE_UNITS = 500
MARKET_MOMENTUM_MIN_PROJECTS = 5

# Scraping
SCRAPER_CONFIDENCE_THRESHOLD = 0.70
PROJECT_MATCH_SIMILARITY_THRESHOLD = 0.85
PRICE_RECONCILE_DIVERGENCE_THRESHOLD = 0.15  # 15% divergence = conflict

# Data quality
MIN_PROJECTS_FOR_DISTRICT_ANALYSIS = 5
MIN_PRICE_RECORDS_FOR_TREND = 3
MAX_DATA_AGE_MONTHS = 6

# Reporting
REPORT_FORECAST_PERIODS = 2
REPORT_CONFIDENCE_LEVEL = 0.95
```

#### 7.3 Environment Variable Support

```python
# Currently: all paths hardcoded in config.py
# Improve: load from .env for deployment flexibility

from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv("MR_DB_PATH", PROJECT_ROOT / "data" / "mr_system.db")
LOG_LEVEL = os.getenv("MR_LOG_LEVEL", "INFO")
SCRAPER_HEADED = os.getenv("MR_SCRAPER_HEADED", "false").lower() == "true"
```

---

### 8. Data Quality Framework

Currently: no systematic data quality checking.

#### 8.1 Completeness Scoring

```python
# src/utils/data_quality.py (new file)

PROJECT_REQUIRED_FIELDS = [
    "name", "developer_id", "district_id", "project_type", "total_units"
]

PROJECT_ENRICHMENT_FIELDS = [
    "price_records",    # has at least 1 price record
    "supply_records",   # has at least 1 supply record
    "unit_types",       # has unit type breakdown
    "facilities",       # has facility list
    "bds_url",          # linked to BDS
]

def score_project_completeness(project: Project) -> float:
    """Returns 0.0-1.0 completeness score."""
```

#### 8.2 Automated Flagging

```python
# Run as part of seeder validation or on-demand

def flag_stale_prices(session, max_age_months=6):
    """Flag price_records with no update in max_age_months."""

def flag_orphaned_projects(session):
    """Projects with no price_records and no scrape history."""

def flag_grade_outliers(session, sigma_threshold=2.5):
    """Price records more than N sigma from their grade mean."""

def flag_absorbed_unsold(session):
    """Projects where sold_units > available_units (data error)."""
```

---

### 9. Seed Data Gaps

#### 9.1 New Seed Files Needed

```
data/seed/
├── macro_indicators.json          # GDP, CPI, interest rates by period
├── regulatory_events.json         # Zoning changes, tax policy events
├── infrastructure_nodes.json      # Metro stations, airports, hospitals
├── developer_track_records.json   # Completion history, quality ratings
├── market_segments_extended.json  # Buyer profiles, income brackets
└── historical_prices.json         # 2018-2022 price history (backfill)
```

#### 9.2 Macro Indicator Schema

```json
{
  "period": "2024-H1",
  "gdp_growth_pct": 6.1,
  "cpi_pct": 4.2,
  "mortgage_rate_pct": 9.5,
  "fdi_usd_billion": 9.27,
  "housing_starts_units": 28000,
  "source": "GSO Vietnam / State Bank of Vietnam"
}
```

---

### 10. UX & Workflow Improvements

#### 10.1 Command Error Handling

```
Current: "/vn-market-briefing xyz" → unhandled error
Proposed: "City 'xyz' not found. Available: HCMC, Hanoi, Binh Duong, Da Nang"
```

Add to all commands:
- Input normalization (case-insensitive, alias lookup)
- Graceful "no data" messages with suggested alternatives
- Data staleness warnings ("Using data from 2023-H2 — more recent data not available")

#### 10.2 Cached Reports

```python
# src/reports/cache.py (new file)

# Cache market briefings (expensive to compute)
# Key: (city, period) → stored markdown
# TTL: 24 hours or until new data seeded
```

#### 10.3 Progress Indicators for Long Operations

```bash
# Current: python -m src.seeders.run_all  (silent)
# Proposed:
[1/17] Seeding cities ✓ (3 records)
[2/17] Seeding districts ✓ (63 records)
[3/17] Seeding grades ✓ (72 records)
...
Done. 227 records seeded in 4.2s
```

---

## Priority Roadmap

### Sprint 10 — Analytical Depth
1. Add temporal trend queries (`get_price_momentum`, `get_supply_demand_ratio`)
2. Implement price forecasting module (`src/reports/price_forecast.py`)
3. Create `/price-forecast` slash command
4. Add macro indicators table + seed data

### Sprint 11 — Data Quality
1. Implement data reconciliation in scraping pipeline
2. Add price anomaly detection
3. Create `data_quality_flags` table
4. Build `/data-quality` command (for internal use)

### Sprint 12 — Developer & Competitive Intelligence
1. Developer scorecard model (`developer_track_records.json`)
2. `/developer-scorecard` command
3. Competitive set queries by location radius
4. `/emerging-districts` command

### Sprint 13 — Output & Distribution
1. HTML report export (Jinja2 → HTML)
2. Excel data export (`openpyxl`)
3. Interactive Plotly charts in briefings
4. PDF export (`weasyprint`)

### Sprint 14 — Predictive & Risk
1. `risk-scorer` agent
2. `/investment-screen` command
3. Supply pipeline forecasting
4. Macro context in market briefings

---

## Impact vs. Effort Matrix

```
HIGH IMPACT
    │
    │  [Macro indicators]    [Price forecasting]
    │  [Data reconciliation] [Developer scorecard]
    │
    │         [Trend queries]  [Anomaly detection]
    │
    │  [Output formats]   [Competitive set queries]
    │
    │         [Risk scorer]    [Scenario analysis]
    │
LOW IMPACT
    └──────────────────────────────────────────────
        LOW EFFORT              HIGH EFFORT
```

**Best ROI (high impact, low effort):**
1. Temporal trend queries — 1-2 days, unlocks forecasting
2. Macro indicators seed data — 1 day, adds critical context
3. Data reconciliation flag — 1 day, prevents bad data
4. Price anomaly detection — 1 day, improves trust
5. `/price-forecast` command — 2-3 days, adds predictive value
