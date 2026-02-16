# Land Review Extraction Summary

**Date:** 2026-02-16
**Extractor:** `src/extractors/land_review_extractor.py`
**Output:** `data/seed/extracted/land_reviews.json`

## Overview

Extracted structured data from 5 NHO-PD land review reports covering 9 land sites across 3 cities in Vietnam.

### Key Statistics

- **Total Records:** 9 land sites
- **Total Land Area:** 367.7 hectares
- **Cities Covered:** Hai Phong (5 sites), Binh Duong (3 sites), Bac Ninh (1 site)
- **Development Types:** Mixed-use (4), Residential (5)
- **Grade Distribution:** M-I (6 sites), M-II (3 sites)

## Source Reports

| Report File | Date | Pages | Sites |
|-------------|------|-------|-------|
| 20250807_NHO-PD_HP-35ha_Proposal_full.txt | 2025-08-07 | 109 | 1 |
| 20250825_NHO-PD_BD_Potential_Land_Review__Revised_full.txt | 2025-08-25 | 17 | 3 |
| 20251017_Hai_Phong_3_Land_review_SWOT_full.txt | 2025-10-17 | 1 | 3 |
| 20251017_NHO-PD_25ha_Duong_Kinh_Land_Review_issued_full.txt | 2025-10-17 | 12 | 1 |
| 20251031_NHO-PD_240ha_Bac_Ninh_Land_Review_full.txt | 2025-10-31 | 43 | 1 |

## Extracted Data by City

### Hai Phong (5 sites, 124.6 ha)

All sites in Duong Kinh and Kien An districts, strategically positioned for Hai Phong's urban expansion.

| Site | District | Area (ha) | Type | Grade | Price (USD/m²) | Competitors |
|------|----------|-----------|------|-------|----------------|-------------|
| 35ha Proposal | Duong Kinh | 35.0 | Mixed-use | M-I | - | 7 |
| 25ha Site 1 | Duong Kinh | 25.4 | Residential | M-I | $1,993 | - |
| 35ha Site 2 | Duong Kinh | 32.0 | Mixed-use | M-I | - | - |
| 7.2ha Site 3 | Kien An | 7.2 | Residential | M-I | $1,354 | - |
| 25ha Issued | Duong Kinh | 25.0 | Mixed-use | M-I | $1,993 | 4 |

**Key Competitors:** Vinhomes Golden City (240ha), Him Lam River City (126ha), Vinhomes Marina, Ecopark, Hoang Huy

**Strategic Context:**
- Between 2 major Economic Zones (Nam Hai Phong EZ & Dinh Vu-Cat Hai EZ)
- Next to Hai Phong New CBD
- Future Ring Road 2 & 3 connectivity
- 5 mins to Admin center, ~10 mins to Cat Bi Airport

### Binh Duong (3 sites, 3.1 ha)

Small-scale residential apartment sites in Thuan An and Thu Dau Mot, targeting end-users and investors.

| Site | District | Area (ha) | Type | Grade | Price (USD/m²) | Zone | Competitors |
|------|----------|-----------|------|-------|----------------|------|-------------|
| A | Thuan An | 1.2 | Residential | M-II | $1,540 | My Phuoc - Tan Van | 7 |
| B | Thuan An | 1.1 | Residential | M-I | $1,620 | National Road 13 | 4 |
| C | Thu Dau Mot | 0.8 | Residential | M-II | - | Thu Dau Mot City | 4 |

**Key Competitors:** Lavita Thuan An, Charm City, Happy One Central, La Pura, A&K Tower

**Market Context:**
- Site A: Along My Phuoc-Tan Van expressway, major logistics corridor, mainly M-II grade
- Site B: Gateway to HCMC, close to AEON Mall and Lotte, H-II and M-I projects
- Site C: Local market, 20km from HCMC, limited upcoming projects

**Infrastructure:**
- Metro Line 1: 32.43km, launching 2027-Q2
- Metro Line 2: 23km, planning stage

### Bac Ninh (1 site, 240.0 ha)

Mega-scale mixed-use development in collaboration with LH Group as master developer.

| Site | District | Area (ha) | Type | Grade | Price (USD/m²) | Role | Competitors |
|------|----------|-----------|------|-------|----------------|------|-------------|
| 240ha | Kim Chan | 240.0 | Mixed-use | M-I | $2,513 | Sub-developer | 4 |

**Key Competitors:** Vinhomes Hoa Long (7.9km, $5,928/m²), Yen Phong Gateway (12km), Sun Group Bac Ninh (19.2km), Him Lam Green Park

**Positioning:** "Bac Ninh Golf-View Gateway City" - greenery urban gateway connecting Bac Ninh and Bac Giang CBDs

**Development Strategy:**
- Zones 1 & 2: Mid-end apartments and low-rise (SH/TH) with early infrastructure
- Zones 3 & 4: High-end villas with lifestyle facilities (clubhouse, theme park, sports center)
- Phasing approach over 2-3 years
- Focus on early sales and cash flow

**Price Benchmarks:**
- Shophouse: ~$4,500/m²
- Townhouse: ~$4,000/m²
- Commercial Apt: $2,160-2,865/m²
- Social Apt: $1,118-1,388/m²

## Data Schema

Each record contains:

### Core Fields
- `report_file`: Source PDF filename
- `report_date`: Report publication date
- `city`, `district`, `ward`: Location hierarchy
- `land_area_ha`: Land size in hectares
- `development_type`: mixed-use | residential | commercial
- `recommended_grade`: H-I, H-II, M-I, M-II, M-III, A-I, A-II
- `benchmark_price_usd_m2`: Representative price point
- `target_products`: Array of product types

### Extended Fields
- `competitor_projects`: Array of competitor names
- `key_competitors`: Detailed competitor data with distances, prices, launch dates
- `positioning`: Market positioning statement
- `target_market`: Target customer segments
- `strengths`, `weaknesses`, `opportunities`, `threats`: SWOT analysis
- `price_ranges`: Detailed pricing by product type
- `market_context`: Grade distribution, infrastructure, etc.
- `development_strategy`: Phasing plans, zones, etc.
- `notes`: Additional observations

### Metadata
- `_meta.source_file`: Original source
- `_meta.pages`: Document page count
- `_meta.confidence`: high | medium | low
- `_meta.extracted_date`: ISO timestamp

## Price Benchmarks Extracted

| City | District | Site | Shophouse | Townhouse | Commercial Apt | Social Apt |
|------|----------|------|-----------|-----------|----------------|------------|
| Hai Phong | Duong Kinh | 25ha Site 1 | $2,142 | $1,844 | - | - |
| Hai Phong | Kien An | 7.2ha Site 3 | - | - | $1,354 | $804 |
| Binh Duong | Thuan An | Site A | - | - | $1,540 | - |
| Binh Duong | Thuan An | Site B | - | - | $1,620 | - |
| Bac Ninh | Kim Chan | 240ha | $4,500 | $4,000 | $2,513 | $1,253 |

## Key Insights

### Market Positioning
1. **Hai Phong:** Focus on mixed-use townships leveraging economic zones and infrastructure
2. **Binh Duong:** Small-scale residential apartments targeting industrial workers and investors
3. **Bac Ninh:** Mega-scale master-planned community with golf-view positioning

### Competitive Landscape
- **Vinhomes:** Dominant across all 3 cities (Golden City, Marina, Vu Yen, Hoa Long)
- **Him Lam:** Major presence in Hai Phong (River City 126ha) and Bac Ninh (Green Park)
- **Regional Players:** Hoang Huy, Ecopark (Hai Phong), Charm Group, SP Setia (Binh Duong)

### Development Strategies
1. **Phasing:** All large sites (>20ha) use phased development
2. **Mixed-Use:** Preferred for large sites to create self-sustaining communities
3. **Infrastructure Timing:** Critical dependency on Ring Roads (RR2, RR3) and metro lines
4. **Market Gaps:** Focus on mid-end (M-I, M-II) grades, avoiding direct luxury competition

### Priority Rankings (3-Land SWOT)
1. **1st Priority:** 35ha Duong Kinh - prime location, current road access, mixed-use zoning
2. **2nd Priority:** 25ha Duong Kinh - strategic location, price advantage, pending road expansion
3. **3rd Priority:** 7.2ha Kien An - central CBD location, but limited access and land use uncertainty

## Data Quality Assessment

### Confidence Levels
- **High Confidence (9/9 records):** All core fields extracted with source page references
- **Partial Data:** Some price benchmarks marked as null where not explicitly stated in reports
- **Competitor Lists:** Comprehensive for Hai Phong and Bac Ninh; more limited for Binh Duong small sites

### Validation Checks
- All land areas verified against report text
- Price conversions: Reports use VND and USD at 1 USD = 25,500 VND
- Distances verified from maps and site analysis sections
- Grade assignments confirmed against NHO-PD's 8-tier system

## Usage Recommendations

### For Database Seeding
- Can be imported as land review records table
- Link to existing `cities`, `districts` via name matching
- Create `competitor_projects` as separate table with many-to-many relationship
- Extract `key_competitors` as separate benchmark records

### For Analysis
- Compare pricing across cities and grades
- Map competitor landscapes by district
- Track infrastructure dependencies
- Analyze development strategy patterns

### For Reporting
- Source citations available via `_meta.source_file` and page numbers
- Confidence scores indicate data reliability
- SWOT fields provide narrative context

## Next Steps

1. **Data Validation:** Cross-reference with existing project database
2. **Competitor Matching:** Link competitor names to existing project records
3. **Price Analysis:** Compare benchmark prices with market data
4. **Location Geocoding:** Add lat/long coordinates for mapping
5. **Infrastructure Overlay:** Link to transportation and amenity data

## Files

- **Extractor Script:** `src/extractors/land_review_extractor.py`
- **Output JSON:** `data/seed/extracted/land_reviews.json` (585 lines, 9 records)
- **This Summary:** `docs/land_review_extraction_summary.md`

---

**Extraction Date:** 2026-02-16
**Confidence:** High
**Status:** Complete - Ready for database integration
