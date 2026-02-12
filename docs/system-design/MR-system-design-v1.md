# MR-System: Vietnam Real Estate Market Research System
## Comprehensive System Design Document v1.0

> Based on analysis of 3 NHO-PD market reports: Binh Duong (241p), HCMC (258p), Hanoi (455p)
> Total: 954 pages, 34 projects, 3 markets analyzed

---

## 1. EXECUTIVE SUMMARY

### 1.1 What the Reports Reveal
NHO-PD(National Housing Organization - Product Development)가 생산하는 보고서는 단순 시장 리포트가 아닌 **경쟁 프로젝트 정밀 벤치마킹 보고서**다. 핵심 목적은:

- 경쟁 프로젝트의 **가격/상품/마케팅/시설/마감재/결제조건**을 브랜드명 수준까지 추적
- 시장 공급/흡수/가격 트렌드를 분기별로 모니터링
- 인프라 개발이 부동산 가치에 미치는 영향 분석
- 자사 프로젝트 포지셔닝 전략 수립 근거 마련

### 1.2 System Goal
이 보고서와 동등하거나 그 이상 수준의 시장분석을 **자동화/반자동화**하는 시스템 구축

### 1.3 Three Reports - Common DNA

| Dimension | Binh Duong | HCMC | Hanoi |
|-----------|-----------|------|-------|
| Pages | 241 | 258 | 455 |
| Projects Analyzed | 10 | 9 | 15 |
| Zone System | 3 zones (NR13, Uni Village, BD New City) | 5 zones (Central, East, South, West, North) | 3 zones (CBD, Outskirts, Suburban) |
| Price Grade | H-II, M-I~III | SL, L, H-I~II, M-I~II, A-I~II | SL, L, H-I~II, M |
| Structure | Market Overview → Conclusion → Grade Comparison → Project Detail | Market Overview → Conclusion → On-Sales/Upcoming → Project Detail | Market Overview → Conclusion → Zone Comparison → Project Detail |
| Template per Project | 10 sections, ~20p each | 10 sections, ~23p each | 11 sections, ~26p each |

---

## 2. DATA ARCHITECTURE

### 2.1 Unified Price Grading System (NHO-PD Proprietary)

```
Super Luxury (SL)  : > 12,000 USD/m2
Luxury (L)         : 5,000 - 11,999 USD/m2
High-end I (H-I)   : 4,000 - 4,999 USD/m2
High-end II (H-II) : 2,500 - 3,999 USD/m2
Mid-end I (M-I)    : 2,000 - 2,499 USD/m2  (HCMC) / 1,600-1,999 (BD)
Mid-end II (M-II)  : 1,500 - 1,999 USD/m2  (HCMC) / 1,200-1,599 (BD)
Mid-end III (M-III) : 1,000 - 1,199 USD/m2  (BD only)
Affordable I (A-I) : 1,300 - 1,499 USD/m2
Affordable II (A-II): < 1,300 USD/m2
```

> Note: Grading thresholds vary by market (BD vs HCMC vs Hanoi). System must store market-specific grade definitions.

### 2.2 Unified Data Schema (Consolidated from 3 Reports)

#### Core Hierarchy
```
Market (City/Province)
  └── Zone (Geographic segment)
       └── District
            └── Complex / Mega-Scale Development (optional)
                 └── Project (Phase + Block level)
                      ├── Unit Types & Layouts
                      ├── Pricing (time-series)
                      ├── Sales Performance (time-series)
                      ├── Facilities
                      ├── Finishing Specs (brand-level)
                      ├── Parking & Shophouse
                      ├── Payment Schedule
                      ├── Marketing & Positioning
                      └── Operation & Management
```

#### Data Categories (Exhaustive Inventory from All 3 Reports)

**A. Geographic & Administrative (7 entity types)**
- Markets (cities/provinces)
- Zones (market-specific segmentation)
- Districts (quan/huyen)
- Wards (phuong/xa)
- Mega-scale developments (Vinhomes, Ciputra, PMH etc.)
- Infrastructure projects (metro, ring roads, bridges, expressways)
- Urban planning zones (master plan 2045-2065)

**B. Project Identity (12 field groups)**
- Project name hierarchy: Complex > Phase > Block
- Developer profile
- Operator/Management company
- Location (address, ward, district, zone)
- Physical specs (land area, blocks, floors, basements, BCR)
- Unit inventory (total + breakdown by type)
- Grade classification
- Timeline (construction, sales, handover)
- Handover condition
- Access control type
- Complex context (for multi-phase projects)
- Construction status & progress

**C. Pricing (8 metrics)**
- Average primary price (USD/m2, excl. VAT)
- Average secondary price (USD/m2)
- Total primary price range (Bil VND)
- Total secondary price range (Bil VND)
- Rumor/expected price
- Price by product type (Apt, SH, OT, Condotel)
- Exchange rate used
- Historical price progression (for phased projects)

**D. Unit Types & Layouts (15 attributes per type)**
- Unit category (Apt, Studio, Duplex, PH, PH DL, SH, Sky Villa, Garden, Loft, Dual-key, Officetel, Condotel, Townhouse)
- Bedroom config (Studio, 1BR, 1.5BR, 2BR, 2.5BR, 3BR, 3.5BR, 4BR, 4.5BR, 5BR, 6BR)
- Bathroom count
- Size range (m2)
- Bay count
- Unit ratio (% of total)
- Floor range allocation
- Units per floor / per core / per lift
- Layout dimensions
- Duplex floor breakdown
- Garden area (for garden units)

**E. Sales Performance (12 metrics)**
- Sales status (Planning, Booking, On-sales, Sold out)
- Total launched vs total inventory
- Units sold & sold percentage
- Sales speed (units/month, units/day)
- Launch event performance (sold % at launch)
- Booking count & velocity
- Booking-to-unit ratio (oversubscription)
- Time to sell out
- Market absorption chart data
- Updated date (near real-time tracking)

**F. Payment Schedule (12 fields)**
- Booking fee (Mil VND)
- Payment timeline (months)
- Number of installments
- Accumulated rate at 3-month intervals
- SPA signing milestone
- Handover payment %
- Pink book extra %
- Maintenance fee %
- Discount percentage
- Developer loan support terms
- Grace period
- Special payment options

**G. Facilities (6 dimensions)**
- Total facility count (range: 13-100+ across reports)
- Floor distribution
- Facility concept
- Itemized facility list with floor location
- Facility category (sport, wellness, kids, social, commercial, landscape)
- Highlight/unique features
- Concierge services
- Operation brand

**H. Finishing Specifications (4 room areas x 8+ components)**
- Living Room & Bedroom: floor, wall, ceiling, balcony balustrade, air-con, wardrobe, shoes cabinet
- Kitchen: floor, wall, ceiling, cabinet, induction, hood, oven, sink/faucet, dishwasher, fridge, microwave, dishrack, island counter
- Bathroom: floor, wall, ceiling, WC/basin, vanity/cabinet, glass partition, water heater, bathtub
- Security: intercom, door lock, doorbell, smart home system
- Each component: material type + brand + provided(Y/N) + upgrade/downgrade flag

**I. Parking & Shophouse (10 fields)**
- Basement floors
- Parking location
- Moto/car slot counts
- Slot per unit ratios
- Shophouse count, rate (%), type (Flat/Duplex/Triplex)
- Mall/Office presence
- Podium scale
- EV charging

**J. Marketing & Positioning (8 fields)**
- Slogan (Vietnamese + English)
- Design concept
- Target customer profile
- Sales points (ranked)
- Marketing content (detailed narrative)
- Marketing images
- Project rendering
- Developer reputation tier

**K. Operation & Management (Hanoi-specific, expanding)**
- Management company
- Management fee (USD/month)
- Car/moto parking fees
- Concierge services list
- Premium services

**L. Macro/Market Data (time-series)**
- New supply (units/quarter)
- Absorption rate (%)
- Average price trend (USD/m2, quarterly)
- Price change QoQ/YoY
- Segment distribution (% by grade)
- FDI inflows
- GRDP growth
- Population & growth rate
- Lending rates
- Government packages

**M. Regulatory & Policy**
- Decree/Decision name & number
- Effective date
- Target (customer/developer/both)
- Impact description
- Source

---

## 3. SYSTEM ARCHITECTURE

### 3.1 Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MR-SYSTEM ARCHITECTURE                          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              LAYER 1: DATA COLLECTION                         │  │
│  │                                                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐   │  │
│  │  │ Web      │ │ News     │ │ Report   │ │ Field Data    │   │  │
│  │  │ Scrapers │ │ Crawlers │ │ Ingestor │ │ Entry Portal  │   │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬────────┘   │  │
│  │       │             │            │               │            │  │
│  │  ┌────┴─────────────┴────────────┴───────────────┴────────┐  │  │
│  │  │              Data Pipeline (ETL/ELT)                    │  │  │
│  │  │    Dedup → Normalize → Validate → Enrich → Load        │  │  │
│  │  └────────────────────────┬────────────────────────────────┘  │  │
│  └───────────────────────────┼───────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────┼───────────────────────────────────┐  │
│  │              LAYER 2: DATA STORAGE                            │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐     │  │
│  │  │ Structured   │  │ Document     │  │ Vector DB      │     │  │
│  │  │ DB (SQLite/  │  │ Store        │  │ (Embeddings    │     │  │
│  │  │ PostgreSQL)  │  │ (PDFs, Imgs, │  │  for semantic  │     │  │
│  │  │              │  │  Floor Plans) │  │  search)       │     │  │
│  │  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘     │  │
│  │         │                 │                    │              │  │
│  │  ┌──────┴─────────────────┴────────────────────┴──────────┐  │  │
│  │  │              Unified Data Access Layer (API)            │  │  │
│  │  └──────────────────────────┬─────────────────────────────┘  │  │
│  └─────────────────────────────┼────────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────────────────────┼────────────────────────────────┐  │
│  │              LAYER 3: ANALYSIS ENGINE                        │  │
│  │                                                               │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │  │
│  │  │ Market     │ │ Competitor │ │ Trend      │ │ Strategy │  │  │
│  │  │ Overview   │ │ Benchmark  │ │ Analysis   │ │ Engine   │  │  │
│  │  │ Agent      │ │ Agent      │ │ Agent      │ │          │  │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────┘  │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐              │  │
│  │  │ Infra      │ │ Price      │ │ Product    │              │  │
│  │  │ Impact     │ │ Grading    │ │ Positioning│              │  │
│  │  │ Agent      │ │ Agent      │ │ Agent      │              │  │
│  │  └────────────┘ └────────────┘ └────────────┘              │  │
│  └─────────────────────────────┬────────────────────────────────┘  │
│                                │                                    │
│  ┌─────────────────────────────┼────────────────────────────────┐  │
│  │              LAYER 4: REPORT GENERATION                      │  │
│  │                                                               │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────────┐   │  │
│  │  │ Template   │ │ Chart      │ │ Multi-language          │   │  │
│  │  │ Engine     │ │ Generator  │ │ (KO/EN/VI)             │   │  │
│  │  └────────────┘ └────────────┘ └────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Collection Sources (Vietnam-Specific)

#### 3.2.1 Real Estate Portals (Web Scraping)
| Source | URL | Data Available | Frequency |
|--------|-----|---------------|-----------|
| batdongsan.com.vn | batdongsan.com.vn | Project listings, prices, developer info, floor plans | Daily |
| cafeland.vn | cafeland.vn | Project listings, news, market data | Daily |
| homedy.com | homedy.com | Listings, price history | Daily |
| chotot.com (nha dat) | nha.chotot.com | Secondary market listings, asking prices | Daily |
| vars.vn | vars.vn | Vietnam Association of Realtors - statistics | Monthly |
| mogi.vn | mogi.vn | Listings, prices | Daily |
| nhadatvui.vn | nhadatvui.vn | Developer project pages | Weekly |

#### 3.2.2 News & Market Intelligence (Crawling)
| Source | URL | Data Type | Frequency |
|--------|-----|-----------|-----------|
| vnexpress.net/bat-dong-san | vnexpress.net | Market news, policy, infrastructure | Daily |
| cafef.vn | cafef.vn | Financial/economic data, RE news | Daily |
| dantri.com.vn | dantri.com.vn | General news, RE section | Daily |
| vietnamnet.vn | vietnamnet.vn | Policy, infrastructure, demographics | Daily |
| vneconomy.vn | vneconomy.vn | Economic indicators, market analysis | Daily |
| tinnhanhchungkhoan.vn | tinnhanhchungkhoan.vn | Financial markets, RE investment | Daily |
| batdongsan.com.vn/tin-tuc | batdongsan.com.vn | Market analysis articles | Daily |

#### 3.2.3 Research Reports (PDF/API Ingestion)
| Source | Data Type | Access Method |
|--------|-----------|---------------|
| CBRE Vietnam | Quarterly market reports | PDF download / email subscription |
| Savills Vietnam | Market outlook, sector reports | PDF download |
| JLL Vietnam | Market insights | PDF download |
| DKRA Vietnam | Southern market reports | PDF download |
| Realplus | Market cycle analysis | PDF / partnership |
| Cushman & Wakefield | Market reports | PDF download |

#### 3.2.4 Government & Official Data
| Source | Data Type | Access |
|--------|-----------|--------|
| gso.gov.vn | General Statistics Office - demographics, GDP, FDI | Web/API |
| moc.gov.vn | Ministry of Construction - housing policies, regulations | Web |
| mpi.gov.vn | Ministry of Planning - FDI data | Web |
| hanoi.gov.vn / hochiminhcity.gov.vn | Local government - infrastructure, planning | Web |
| thuvienphapluat.vn | Legal database - decrees, regulations | Web |

#### 3.2.5 Developer Direct Sources
| Type | Examples | Method |
|------|----------|--------|
| Developer websites | vinhomes.vn, masgroup.vn, masterisehomes.com | Web scraping |
| Project microsites | Individual project landing pages | Web scraping |
| Social media | Facebook pages/groups, Zalo groups | API/scraping |
| Sales events | Booking/launch event monitoring | Manual + alerts |

---

## 4. AGENT & SKILL ARCHITECTURE

### 4.1 Sub-Agents (Claude Code)

#### Agent 1: `data-collector` - Data Collection Orchestrator
```yaml
name: data-collector
description: Orchestrates web scraping, news crawling, and data ingestion
tools: [Bash, Read, Write, WebFetch, WebSearch, Glob, Grep]
responsibilities:
  - Schedule and execute web scraping jobs
  - Parse and normalize collected data
  - Detect new project launches and price changes
  - Monitor infrastructure development news
  - Ingest PDF reports from CBRE/Savills/DKRA
triggers:
  - Scheduled: daily news, weekly listings, monthly reports
  - On-demand: specific project research
```

#### Agent 2: `market-analyzer` - Market Analysis Engine
```yaml
name: market-analyzer
description: Analyzes market data and produces insights
tools: [Read, WebSearch, WebFetch, Bash, Glob, Grep]
responsibilities:
  - Generate market overview (supply, demand, price trends)
  - Calculate absorption rates and sales velocity
  - Track price grade distribution changes
  - Assess infrastructure impact on property values
  - Compare market cycles across cities
  - Produce zone-level analysis
```

#### Agent 3: `competitor-benchmarker` - Competitive Intelligence
```yaml
name: competitor-benchmarker
description: Deep-dive analysis of competing projects
tools: [Read, Write, WebSearch, WebFetch, Bash, Glob, Grep]
responsibilities:
  - Build and maintain project profiles (all 50+ attributes)
  - Compare projects across 11 standardized dimensions
  - Track finishing specs at brand level
  - Monitor sales performance and pricing changes
  - Identify upgrade/downgrade positioning
  - Benchmark payment schedules
```

#### Agent 4: `strategy-advisor` - Strategy Formulation
```yaml
name: strategy-advisor
description: Synthesizes analysis into strategic recommendations
tools: [Read, WebSearch, Glob, Grep]
responsibilities:
  - Pricing strategy recommendations
  - Unit mix optimization suggestions
  - Facility strategy based on competitive landscape
  - Finishing spec recommendations (brand/material selection)
  - Payment structure optimization
  - Marketing positioning advice
  - Launch timing recommendations
```

#### Agent 5: `report-generator` - Report Production
```yaml
name: report-generator
description: Generates formatted market analysis reports
tools: [Read, Write, Bash, Glob]
responsibilities:
  - Produce NHO-PD style market reports
  - Generate comparison tables and matrices
  - Create executive summaries and conclusions
  - Multi-language output (Korean, English, Vietnamese)
  - Export to various formats (Markdown, PDF, PPTX)
```

### 4.2 Skills (Claude Code Slash Commands)

#### Skill 1: `/vn-market-briefing`
```
Trigger: "베트남 시장 브리핑", "Vietnam market update"
Function: 최신 시장 데이터 수집 + 요약 브리핑 생성
Output: 시장 개요, 주요 변동사항, 신규 프로젝트, 인프라 업데이트
```

#### Skill 2: `/project-profile {project_name}`
```
Trigger: "프로젝트 분석", "analyze project"
Function: 특정 프로젝트의 11차원 프로파일 생성
Output: NHO-PD 템플릿 수준의 프로젝트 분석 보고서
```

#### Skill 3: `/competitor-compare {project1} {project2} ...`
```
Trigger: "경쟁 비교", "compare projects"
Function: 선택한 프로젝트들의 side-by-side 비교 분석
Output: 비교 매트릭스 (가격, 상품, 시설, 마감재, 결제조건 등)
```

#### Skill 4: `/zone-analysis {city} {zone}`
```
Trigger: "존 분석", "zone analysis"
Function: 특정 도시/존의 시장 분석
Output: 존별 공급/수요/가격/경쟁 현황
```

#### Skill 5: `/price-strategy {project_params}`
```
Trigger: "가격 전략", "pricing strategy"
Function: 기존 데이터 기반 가격 포지셔닝 제안
Output: 권장 가격대, 근거 분석, 비교 프로젝트 벤치마크
```

#### Skill 6: `/data-update`
```
Trigger: "데이터 업데이트", "update data"
Function: 모든 수집 소스에서 최신 데이터 수집
Output: 업데이트 요약, 변동사항 하이라이트
```

#### Skill 7: `/full-report {city} {year}`
```
Trigger: "시장 보고서 생성", "generate market report"
Function: NHO-PD 수준의 전체 시장분석 보고서 생성
Output: Part 1 (Market Overview) + Part 2 (Project Analysis) + Appendix (Project Details)
```

### 4.3 Hooks (Automation Triggers)

```yaml
# Auto-update on new data detection
- event: PostToolUse
  tool: data-collector
  action: "Check for significant changes and alert"

# Quality check on generated reports
- event: PostToolUse
  tool: report-generator
  action: "Validate data consistency and completeness"
```

---

## 5. DATA COLLECTION IMPLEMENTATION

### 5.1 Web Scraping Architecture

```
┌──────────────────────────────────────────────┐
│           Scraping Pipeline                   │
│                                               │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐ │
│  │ Scrapy / │    │ Selenium │    │ API     │ │
│  │ BeautifulSoup│ │ (JS-heavy│    │ Clients │ │
│  │ (Static) │    │  sites)  │    │         │ │
│  └────┬─────┘    └────┬─────┘    └────┬────┘ │
│       │               │               │      │
│  ┌────┴───────────────┴───────────────┴────┐ │
│  │         Proxy Rotation Layer            │ │
│  │   (Vietnam IP / Rotating Residential)   │ │
│  └────────────────────┬────────────────────┘ │
│                       │                       │
│  ┌────────────────────┴────────────────────┐ │
│  │      Rate Limiter & Request Queue       │ │
│  │   (Respect robots.txt, polite delays)   │ │
│  └────────────────────┬────────────────────┘ │
│                       │                       │
│  ┌────────────────────┴────────────────────┐ │
│  │         Parser & Normalizer             │ │
│  │   (Extract → Clean → Validate → Store)  │ │
│  └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

### 5.2 Scraping Targets & Data Mapping

#### batdongsan.com.vn (Primary Source)
```yaml
target_pages:
  project_listing: /du-an-bat-dong-san
  project_detail: /du-an/{project-slug}
  price_history: /gia-nha-dat/{location}
  news: /tin-tuc

extractable_data:
  project_level:
    - project_name, developer, location (district, city)
    - price_range (VND/m2), total_price
    - unit_types, unit_sizes
    - project_status (upcoming, on_sale, completed)
    - facilities_list
    - floor_plan_images
    - project_description
  market_level:
    - average_price_by_district
    - listing_volume_trends
    - price_change_indicators
```

#### Developer Websites (Per-Project Deep Data)
```yaml
target_pattern: "{developer-domain}/project/{project-name}"
extractable_data:
  - detailed_floor_plans
  - unit_layout_images
  - payment_schedule_details
  - finishing_specification
  - facility_renderings
  - sales_event_announcements
  - brochure_PDFs
```

### 5.3 News Monitoring System

```yaml
sources:
  - vnexpress.net/bat-dong-san
  - cafef.vn/bat-dong-san
  - dantri.com.vn/bat-dong-san
  - vietnamnet.vn/bat-dong-san
  - vneconomy.vn/bat-dong-san

monitoring_keywords:
  market: ["thi truong bat dong san", "gia nha dat", "cung cau"]
  infrastructure: ["metro", "vanh dai", "cao toc", "cau", "san bay"]
  policy: ["nghi dinh", "luat nha o", "quy hoach", "chinh sach"]
  projects: ["du an moi", "mo ban", "khoi cong", "ban giao"]
  economic: ["FDI", "GDP", "lai suat", "tin dung"]

output:
  - Daily summary (deduplicated, categorized)
  - Alert on significant events (new project launch, policy change, etc.)
  - Weekly trend analysis
```

### 5.4 PDF Report Ingestion Pipeline

```
PDF Input → Text Extraction (PyMuPDF) → Structure Detection
  → Table Extraction (Camelot/Tabula) → Image Extraction
    → NLP Classification (section type) → Data Normalization
      → Database Insert
```

---

## 6. DATABASE SCHEMA (Production-Ready)

### 6.1 Core Tables

```sql
-- =============================================
-- MARKET & GEOGRAPHY
-- =============================================

CREATE TABLE markets (
    id              SERIAL PRIMARY KEY,
    name_en         VARCHAR(100) NOT NULL,
    name_vi         VARCHAR(100),
    name_ko         VARCHAR(100),
    country         VARCHAR(50) DEFAULT 'Vietnam',
    land_area_km2   DECIMAL(12,2),
    population      INTEGER,
    pop_growth_pct  DECIMAL(5,4),
    grdp_growth_pct DECIMAL(5,2),
    fdi_usd_bil     DECIMAL(12,2),
    gdp_share_pct   DECIMAL(5,2),
    data_as_of      DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE grade_definitions (
    id              SERIAL PRIMARY KEY,
    market_id       INTEGER REFERENCES markets(id),
    grade_code      VARCHAR(10) NOT NULL,   -- SL, L, H-I, H-II, M-I, M-II, M-III, A-I, A-II
    grade_name      VARCHAR(50),
    price_min_usd   DECIMAL(10,2),
    price_max_usd   DECIMAL(10,2),
    valid_from      DATE,
    valid_to        DATE
);

CREATE TABLE zones (
    id              SERIAL PRIMARY KEY,
    market_id       INTEGER REFERENCES markets(id),
    zone_code       VARCHAR(20) NOT NULL,   -- ZONE_I, CENTRAL, EASTERN etc.
    zone_name_en    VARCHAR(100),
    zone_name_vi    VARCHAR(100),
    zone_type       VARCHAR(30),            -- analysis_zone, urban_plan_zone
    description     TEXT,
    price_range_min DECIMAL(10,2),
    price_range_max DECIMAL(10,2),
    project_count   INTEGER
);

CREATE TABLE districts (
    id              SERIAL PRIMARY KEY,
    market_id       INTEGER REFERENCES markets(id),
    zone_id         INTEGER REFERENCES zones(id),
    name_en         VARCHAR(100),
    name_vi         VARCHAR(100),
    code            VARCHAR(20),            -- D1, D2, etc.
    district_type   VARCHAR(20),            -- urban, suburban, town
    area_km2        DECIMAL(10,2),
    population      INTEGER,
    is_active       BOOLEAN DEFAULT TRUE
);

-- =============================================
-- DEVELOPERS & COMPLEXES
-- =============================================

CREATE TABLE developers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    name_vi         VARCHAR(200),
    country_origin  VARCHAR(50),
    reputation_tier VARCHAR(20),            -- well_known, established, new
    description     TEXT,
    website         VARCHAR(500)
);

CREATE TABLE complexes (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    abbreviation    VARCHAR(20),            -- VHSC, VHGG, VHOP1, PMH
    district_id     INTEGER REFERENCES districts(id),
    master_developer_id INTEGER REFERENCES developers(id),
    total_area_ha   DECIMAL(12,2),
    complex_type    VARCHAR(50),            -- township, mixed_use, standalone
    identity_feature TEXT,
    description     TEXT
);

-- =============================================
-- PROJECTS (Core Entity)
-- =============================================

CREATE TABLE projects (
    id                  SERIAL PRIMARY KEY,
    complex_id          INTEGER REFERENCES complexes(id),
    developer_id        INTEGER REFERENCES developers(id),
    district_id         INTEGER REFERENCES districts(id),
    zone_id             INTEGER REFERENCES zones(id),

    -- Identity
    project_name        VARCHAR(300) NOT NULL,
    project_name_full   VARCHAR(500),       -- Complex > Phase > Block
    phase               VARCHAR(50),
    block               VARCHAR(100),
    grade_code          VARCHAR(10),

    -- Location
    address             TEXT,
    ward_vi             VARCHAR(100),

    -- Physical
    land_area_m2        DECIMAL(12,2),
    total_blocks        INTEGER,
    total_floors        VARCHAR(50),        -- "37-44F" format
    basements           INTEGER,
    bcr_pct             DECIMAL(5,2),
    total_units         INTEGER,
    apt_units           INTEGER,
    sh_units            INTEGER,
    ph_units            INTEGER,
    dl_units            INTEGER,
    ph_dl_units         INTEGER,
    sky_villa_units     INTEGER,
    ot_units            INTEGER,            -- officetel
    condotel_units      INTEGER,
    loft_units          INTEGER,
    garden_units        INTEGER,
    dual_key_units      INTEGER,
    other_units         INTEGER,

    -- Timeline
    construction_launch DATE,
    sales_launch        DATE,
    handover_date       DATE,

    -- Condition
    handover_condition  VARCHAR(100),        -- basic_finishing, bare_shell, full_furniture
    access_control      VARCHAR(50),         -- open_type, gated_type

    -- Management
    operator_name       VARCHAR(200),
    mgmt_fee_usd_month  DECIMAL(8,2),
    car_fee_usd_month   DECIMAL(8,2),
    moto_fee_usd_month  DECIMAL(8,2),

    -- Flags
    is_branded_residence BOOLEAN DEFAULT FALSE,
    brand_operator      VARCHAR(100),
    is_multi_phase      BOOLEAN DEFAULT FALSE,

    -- Metadata
    data_source         VARCHAR(200),
    last_verified       DATE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- PRICING (Time-Series)
-- =============================================

CREATE TABLE project_pricing (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    price_type          VARCHAR(20) NOT NULL,   -- primary, secondary, rumor
    product_type        VARCHAR(30),            -- apartment, shophouse, officetel, etc.
    avg_price_usd_m2    DECIMAL(10,2),
    avg_price_vnd_m2    DECIMAL(15,2),
    total_price_min_bil_vnd DECIMAL(10,2),
    total_price_max_bil_vnd DECIMAL(10,2),
    exchange_rate       DECIMAL(10,2),
    excl_vat            BOOLEAN DEFAULT TRUE,
    checked_date        DATE,
    source              VARCHAR(200),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE phase_price_progression (
    id                  SERIAL PRIMARY KEY,
    complex_id          INTEGER REFERENCES complexes(id),
    phase_name          VARCHAR(100),
    developer           VARCHAR(200),
    launch_date         DATE,
    avg_price_usd_m2    DECIMAL(10,2),
    total_units         INTEGER,
    status              VARCHAR(30)
);

-- =============================================
-- UNIT TYPES & LAYOUTS
-- =============================================

CREATE TABLE unit_types (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES projects(id),
    unit_category   VARCHAR(30),            -- apartment, duplex, penthouse, etc.
    bedroom_config  VARCHAR(20),            -- Studio, 1BR, 1.5BR, 2BR, etc.
    bathroom_count  INTEGER,
    size_min_m2     DECIMAL(8,2),
    size_max_m2     DECIMAL(8,2),
    bay_count       DECIMAL(3,1),
    unit_count      INTEGER,
    ratio_pct       DECIMAL(5,2),
    floor_range     VARCHAR(100),
    is_most_units   BOOLEAN DEFAULT FALSE,
    has_garden      BOOLEAN DEFAULT FALSE,
    garden_area_m2  DECIMAL(8,2)
);

CREATE TABLE typical_floors (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES projects(id),
    floor_range     VARCHAR(100),
    units_per_floor INTEGER,
    cores_count     INTEGER,
    units_per_lift  INTEGER
);

CREATE TABLE unit_layouts (
    id              SERIAL PRIMARY KEY,
    unit_type_id    INTEGER REFERENCES unit_types(id),
    layout_name     VARCHAR(100),
    area_m2         DECIMAL(8,2),
    bay_count       DECIMAL(3,1),
    floor_range     VARCHAR(100),
    image_path      VARCHAR(500)
);

-- =============================================
-- SALES PERFORMANCE (Time-Series)
-- =============================================

CREATE TABLE sales_status (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES projects(id),
    status          VARCHAR(30),            -- planning, booking, on_sales, sold_out
    total_launched  INTEGER,
    total_inventory INTEGER,
    units_sold      INTEGER,
    sold_pct        DECIMAL(5,2),
    sales_speed_per_month DECIMAL(10,2),
    time_to_sell    VARCHAR(100),
    bookings_count  INTEGER,
    booking_ratio   DECIMAL(5,2),           -- bookings / available units
    remark          TEXT,
    updated_at      DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sales_events (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES projects(id),
    event_type      VARCHAR(30),            -- kickoff, booking, launching, phase_launch
    event_date      DATE,
    released_units  INTEGER,
    sold_units      INTEGER,
    sold_pct        DECIMAL(5,2),
    bookings        INTEGER,
    duration        VARCHAR(50),
    remark          TEXT
);

-- =============================================
-- PAYMENT SCHEDULES
-- =============================================

CREATE TABLE payment_schedules (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    booking_fee_mil_vnd DECIMAL(10,2),
    timeline_months     INTEGER,
    num_installments    INTEGER,
    handover_pct        DECIMAL(5,2),
    pink_book_pct       DECIMAL(5,2),
    maintenance_fee_pct DECIMAL(5,2),
    discount_pct        DECIMAL(5,2),
    spa_signing_month   INTEGER,
    loan_support_months INTEGER,
    loan_interest_rate  DECIMAL(5,2),
    remark              TEXT
);

CREATE TABLE payment_milestones (
    id              SERIAL PRIMARY KEY,
    schedule_id     INTEGER REFERENCES payment_schedules(id),
    month           INTEGER,
    accumulated_pct DECIMAL(5,2),
    label           VARCHAR(100)            -- "Sign SPA", "Handover", "Pink book"
);

-- =============================================
-- FACILITIES
-- =============================================

CREATE TABLE project_facilities (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    total_count         INTEGER,
    floor_distribution  VARCHAR(200),
    facility_concept    TEXT,
    highlight_features  TEXT
);

CREATE TABLE facility_items (
    id              SERIAL PRIMARY KEY,
    facility_id     INTEGER REFERENCES project_facilities(id),
    name            VARCHAR(200),
    floor_location  VARCHAR(20),
    category        VARCHAR(50),            -- sport, wellness, kids, social, commercial, landscape
    is_indoor       BOOLEAN
);

-- =============================================
-- FINISHING SPECIFICATIONS
-- =============================================

CREATE TABLE finishing_specs (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES projects(id),
    room_area       VARCHAR(30),            -- living_room, bedroom, kitchen, bathroom, security
    component       VARCHAR(100),           -- floor, wall, ceiling, air_con, cabinet, etc.
    material_type   VARCHAR(200),
    brand           VARCHAR(300),
    is_provided     BOOLEAN DEFAULT TRUE,
    upgrade_flag    VARCHAR(5),             -- '+', '-', NULL
    specification   VARCHAR(200),
    remark          TEXT
);

-- =============================================
-- PARKING & SHOPHOUSE
-- =============================================

CREATE TABLE parking (
    id                  SERIAL PRIMARY KEY,
    project_id          INTEGER REFERENCES projects(id),
    basement_floors     INTEGER,
    parking_location    TEXT,
    moto_slots          INTEGER,
    car_slots           INTEGER,
    moto_per_unit       DECIMAL(4,2),
    car_per_unit        DECIMAL(4,2),
    has_ev_charging     BOOLEAN DEFAULT FALSE
);

CREATE TABLE shophouse_details (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES projects(id),
    sh_count        INTEGER,
    sh_rate_pct     DECIMAL(5,2),
    sh_type         VARCHAR(30),            -- Flat, Duplex, Triplex
    podium_floors   INTEGER,
    has_mall        BOOLEAN DEFAULT FALSE,
    has_office      BOOLEAN DEFAULT FALSE
);

-- =============================================
-- MARKETING
-- =============================================

CREATE TABLE project_marketing (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER REFERENCES projects(id),
    slogan_en       TEXT,
    slogan_vi       TEXT,
    design_concept  VARCHAR(200),
    target_customer TEXT,
    sales_points    TEXT,                    -- JSON array
    mkt_content     TEXT,
    image_path      VARCHAR(500)
);

-- =============================================
-- INFRASTRUCTURE
-- =============================================

CREATE TABLE infrastructure (
    id              SERIAL PRIMARY KEY,
    market_id       INTEGER REFERENCES markets(id),
    name            VARCHAR(200) NOT NULL,
    infra_type      VARCHAR(30),            -- metro, ring_road, bridge, expressway, main_road
    length_km       DECIMAL(8,2),
    lanes           INTEGER,
    stations        INTEGER,
    status          VARCHAR(30),            -- completed, under_construction, planning
    start_date      VARCHAR(20),
    completion_date VARCHAR(20),
    completion_pct  DECIMAL(5,2),
    investment_bil_vnd DECIMAL(15,2),
    remark          TEXT,
    updated_at      DATE
);

-- =============================================
-- MARKET TIME-SERIES DATA
-- =============================================

CREATE TABLE market_supply_quarterly (
    id              SERIAL PRIMARY KEY,
    market_id       INTEGER REFERENCES markets(id),
    year            INTEGER,
    quarter         INTEGER,
    new_supply_units INTEGER,
    cumulative_supply INTEGER,
    sold_units      INTEGER,
    remaining_units INTEGER,
    absorption_pct  DECIMAL(5,2),
    source          VARCHAR(100)
);

CREATE TABLE market_price_quarterly (
    id              SERIAL PRIMARY KEY,
    market_id       INTEGER REFERENCES markets(id),
    year            INTEGER,
    quarter         INTEGER,
    avg_price_usd_m2 DECIMAL(10,2),
    avg_price_vnd_m2 DECIMAL(15,2),
    change_qoq_pct DECIMAL(5,2),
    change_yoy_pct DECIMAL(5,2),
    source          VARCHAR(100)
);

CREATE TABLE segment_distribution (
    id              SERIAL PRIMARY KEY,
    market_id       INTEGER REFERENCES markets(id),
    zone_id         INTEGER REFERENCES zones(id),
    year            INTEGER,
    half            INTEGER,                -- 1 or 2
    grade_code      VARCHAR(10),
    supply_share_pct DECIMAL(5,2),
    project_count   INTEGER
);

-- =============================================
-- REGULATIONS & POLICY
-- =============================================

CREATE TABLE regulations (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200),
    number          VARCHAR(100),           -- Decree 261, Decision 1668
    effective_date  DATE,
    status          VARCHAR(20),            -- official, draft, expired
    target          VARCHAR(50),            -- customer, developer, both
    description     TEXT,
    impact_summary  TEXT,
    source_url      VARCHAR(500)
);

-- =============================================
-- NEWS & INTELLIGENCE
-- =============================================

CREATE TABLE news_articles (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(100),
    url             VARCHAR(1000),
    title           TEXT,
    title_translated TEXT,                  -- Korean translation
    content_summary TEXT,
    category        VARCHAR(50),            -- market, infrastructure, policy, project, economic
    market_id       INTEGER REFERENCES markets(id),
    published_date  DATE,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    relevance_score DECIMAL(3,2)
);

-- =============================================
-- REPORT TRACKING
-- =============================================

CREATE TABLE reports (
    id              SERIAL PRIMARY KEY,
    report_type     VARCHAR(50),            -- market_analysis, project_profile, competitor_compare
    market_id       INTEGER REFERENCES markets(id),
    title           VARCHAR(300),
    author          VARCHAR(100),
    report_date     DATE,
    file_path       VARCHAR(500),
    status          VARCHAR(20),            -- draft, published
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- DATA COLLECTION LOG
-- =============================================

CREATE TABLE collection_log (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(200),
    collection_type VARCHAR(50),            -- scraping, crawling, pdf_ingestion, manual
    items_collected INTEGER,
    items_new       INTEGER,
    items_updated   INTEGER,
    status          VARCHAR(20),            -- success, partial, failed
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);
```

---

## 7. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 1-2)
```
[x] Analyze existing reports (DONE)
[ ] Set up project structure
[ ] Initialize database (SQLite for development → PostgreSQL for production)
[ ] Create data models (Python/TypeScript)
[ ] Build data import tool for existing PDF reports
[ ] Seed database with data from 3 analyzed reports (34 projects)
```

### Phase 2: Data Collection Infrastructure (Week 3-4)
```
[ ] Build web scraping framework (Scrapy/Playwright)
[ ] Implement batdongsan.com.vn scraper (primary source)
[ ] Implement news crawler (vnexpress, cafef, dantri)
[ ] Build PDF report ingestion pipeline (CBRE, Savills, DKRA)
[ ] Set up proxy rotation for Vietnam IPs
[ ] Create scheduling system (daily/weekly/monthly jobs)
[ ] Build data validation & deduplication pipeline
```

### Phase 3: Agent System (Week 5-6)
```
[ ] Create data-collector sub-agent
[ ] Create market-analyzer sub-agent
[ ] Create competitor-benchmarker sub-agent
[ ] Create strategy-advisor sub-agent
[ ] Create report-generator sub-agent
[ ] Build inter-agent communication protocol
```

### Phase 4: Skills & Commands (Week 7-8)
```
[ ] Build /vn-market-briefing skill
[ ] Build /project-profile skill
[ ] Build /competitor-compare skill
[ ] Build /zone-analysis skill
[ ] Build /price-strategy skill
[ ] Build /data-update skill
[ ] Build /full-report skill
```

### Phase 5: Report Generation (Week 9-10)
```
[ ] Design report templates (matching NHO-PD style)
[ ] Build comparison table generator
[ ] Build chart/visualization generator
[ ] Implement multi-language support (KO/EN/VI)
[ ] Create PDF/PPTX export pipeline
```

### Phase 6: Testing & Refinement (Week 11-12)
```
[ ] End-to-end testing with real data
[ ] Validate output against original NHO-PD reports
[ ] Performance optimization
[ ] Error handling & monitoring
[ ] Documentation
```

---

## 8. TECHNOLOGY STACK

### 8.1 Recommended Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Python 3.12+ | Best ecosystem for scraping, data processing, ML |
| **Database** | SQLite (dev) → PostgreSQL (prod) | Start simple, scale when needed |
| **ORM** | SQLAlchemy / Prisma | Type-safe database access |
| **Web Scraping** | Scrapy + Playwright | Static + JS-rendered pages |
| **PDF Processing** | PyMuPDF + Camelot + pdfplumber | Text + table + image extraction |
| **NLP** | Claude API (Sonnet for processing, Opus for analysis) | Report understanding & generation |
| **Vector DB** | ChromaDB / FAISS | Semantic search across reports |
| **Scheduling** | APScheduler / Cron | Job scheduling |
| **Report Generation** | python-pptx + matplotlib + Jinja2 | PPTX/PDF output |
| **Proxy** | Bright Data / ScraperAPI | Vietnam IP rotation |
| **Agent Framework** | Claude Code Sub-agents | Analysis & strategy agents |

### 8.2 File Structure (Proposed)

```
MR-system/
├── .claude/
│   ├── agents/
│   │   ├── data-collector.md
│   │   ├── market-analyzer.md
│   │   ├── competitor-benchmarker.md
│   │   ├── strategy-advisor.md
│   │   └── report-generator.md
│   ├── commands/
│   │   ├── vn-market-briefing.md
│   │   ├── project-profile.md
│   │   ├── competitor-compare.md
│   │   ├── zone-analysis.md
│   │   ├── price-strategy.md
│   │   ├── data-update.md
│   │   └── full-report.md
│   └── settings.json
├── src/
│   ├── collectors/
│   │   ├── scrapers/
│   │   │   ├── batdongsan.py
│   │   │   ├── cafeland.py
│   │   │   ├── developer_sites.py
│   │   │   └── base_scraper.py
│   │   ├── crawlers/
│   │   │   ├── news_crawler.py
│   │   │   └── government_crawler.py
│   │   ├── ingestors/
│   │   │   ├── pdf_ingestor.py
│   │   │   └── report_parser.py
│   │   └── pipeline.py
│   ├── database/
│   │   ├── models.py
│   │   ├── schema.sql
│   │   ├── migrations/
│   │   └── seed/
│   ├── analysis/
│   │   ├── market_overview.py
│   │   ├── competitor_benchmark.py
│   │   ├── trend_analysis.py
│   │   ├── price_strategy.py
│   │   ├── infra_impact.py
│   │   └── product_positioning.py
│   ├── reports/
│   │   ├── templates/
│   │   │   ├── market_overview.jinja2
│   │   │   ├── project_profile.jinja2
│   │   │   ├── comparison_table.jinja2
│   │   │   └── full_report.jinja2
│   │   ├── generators/
│   │   │   ├── markdown_gen.py
│   │   │   ├── pptx_gen.py
│   │   │   └── chart_gen.py
│   │   └── localization/
│   │       ├── ko.json
│   │       ├── en.json
│   │       └── vi.json
│   └── utils/
│       ├── currency.py
│       ├── date_utils.py
│       ├── proxy_manager.py
│       └── validators.py
├── data/
│   ├── db/
│   │   └── mr_system.db
│   ├── raw/                    # Raw collected data
│   ├── processed/              # Cleaned & normalized
│   ├── reports/                # Generated reports
│   └── media/                  # Images, floor plans, PDFs
├── tests/
├── docs/
│   ├── system-design/
│   └── api/
├── user_resources/             # User-provided reference files
│   └── D_colect/
├── CLAUDE.md
├── requirements.txt
└── README.md
```

---

## 9. CRITICAL SUCCESS FACTORS

### 9.1 Data Quality
- **Deduplication**: Same project may appear on multiple sources with different names
- **Normalization**: Price formats (VND vs USD), area formats (m2), date formats vary
- **Currency tracking**: USD/VND rate must be recorded with each price data point
- **Vietnamese text handling**: Proper UTF-8, diacritical marks (e.g., phường vs phuong)
- **Version control**: Track data changes over time, not just latest snapshot

### 9.2 Scraping Sustainability
- **Rate limiting**: Respectful crawling to avoid IP bans
- **Proxy rotation**: Vietnam-based residential proxies for local content
- **robots.txt compliance**: Follow site rules
- **Fallback sources**: Multiple sources for each data type
- **Anti-bot detection**: Playwright for JS-heavy sites, header rotation

### 9.3 Analysis Accuracy
- **Grade calibration**: NHO-PD grades vary by market - must be market-aware
- **Comparison fairness**: Only compare projects within same grade and zone
- **Temporal alignment**: Compare data from same time period
- **Source attribution**: Always track where each data point came from

### 9.4 Report Quality
- **Template fidelity**: Match NHO-PD report structure and depth
- **Data completeness**: Flag missing data rather than omit silently
- **Multi-language**: Korean for internal team, English for international, Vietnamese for local
- **Visual consistency**: Standardized charts, tables, and formatting

---

## 10. WHAT YOU MIGHT NOT HAVE CONSIDERED

### 10.1 Legal & Compliance
- Vietnam's Cybersecurity Law (2018) and Personal Data Protection Decree (2023)
- Terms of service for scraped websites
- Intellectual property considerations for collected market data
- NHO-PD report confidentiality classification

### 10.2 Data Freshness Strategy
- **Hot data** (update daily): News, new project announcements, policy changes
- **Warm data** (update weekly): Listing prices, project status changes
- **Cool data** (update monthly): Sales performance, absorption rates
- **Cold data** (update quarterly): Market supply/demand, macro indicators
- **Static data** (update per event): Floor plans, finishing specs, payment schedules

### 10.3 Competitive Intelligence Ethics
- Publicly available information only for automated collection
- Developer marketing materials = public domain
- Sales event data = can be collected through legitimate attendance
- Internal competitor data (NHO-PD style deep specs) = requires field research

### 10.4 Vietnam-Specific Technical Challenges
- **Language**: Vietnamese with diacritics, mixed Vietnamese-English content
- **Currency**: VND is a high-number currency (billions in property prices)
- **Internet**: Vietnam has restricted access to some services
- **Government data**: Often in image/PDF format, not machine-readable
- **Developer websites**: Often Flash-era quality, inconsistent structures
- **Social commerce**: Facebook/Zalo groups are major RE channels in Vietnam

### 10.5 Historical Data Bootstrap
- The 3 existing reports contain data on 34 projects - this is your seed dataset
- CBRE/Savills publish quarterly reports - historical data going back to 2015+
- batdongsan.com.vn has historical listing data
- Need a one-time "backfill" effort to build the historical baseline

### 10.6 Monitoring & Alerting
- **New project alert**: When a new project appears on any source
- **Price change alert**: When a tracked project's price changes significantly
- **Policy alert**: When new regulations affect the market
- **Infrastructure milestone**: When a key infrastructure project reaches a milestone
- **Sales event alert**: When a competitor announces a launch event
- **Report due reminder**: When it's time to generate periodic reports

### 10.7 Image/Visual Data
- Floor plan images need OCR or manual annotation for structured data
- Rendering images useful for marketing analysis
- Construction progress photos need dated tracking
- Master plan maps need geographic tagging
- Consider using Claude's vision capabilities for image analysis

### 10.8 Collaboration Features
- Multiple analysts may work on same market
- Comments and annotations on data points
- Approval workflow for published reports
- Audit trail for data changes

---

## 11. IMMEDIATE NEXT STEPS

1. **Confirm scope**: Vietnam first (HCMC, Hanoi, Binh Duong) - confirmed
2. **Choose starting point**: Database + seed data from existing reports
3. **Build first scraper**: batdongsan.com.vn (highest data density)
4. **Create first agent**: data-collector (foundation for everything else)
5. **Seed database**: Import 34 projects from analyzed PDFs
6. **First skill**: /vn-market-briefing (quickest value delivery)
