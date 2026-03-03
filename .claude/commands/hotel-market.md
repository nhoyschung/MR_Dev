# /hotel-market — Hotel Market Analysis

Analyze the HCMC hotel market: property profiles, performance KPIs (occupancy, ADR, RevPAR), and trend analysis.

## Usage
```
/hotel-market [city] [year] [half] [optional: district | hotel name | star rating]
```

**Examples:**
- `/hotel-market hcmc 2024 H2` — Citywide hotel market overview
- `/hotel-market hcmc 2024 H2 "Thao Dien"` — Thao Dien submarket analysis
- `/hotel-market hcmc 2024 H2 "Mozac Hotel"` — Single property profile with room breakdown
- `/hotel-market hcmc 2024 H2 4star` — 4-star hotel segment

## Instructions

Parse arguments from `$ARGUMENTS`. Default city = "Ho Chi Minh City", default period = most recent available.

### Step 1 — Market KPIs

```python
from src.db.connection import get_session
from src.db.queries import get_hotel_market_performance, get_hotel_kpi_trend

with get_session() as s:
    perf = get_hotel_market_performance(s, city_name, year, half)
    trend = get_hotel_kpi_trend(s, city_name)
```

Report key metrics for the period:
- Total rooms, total properties
- Occupancy rate (%)
- ADR — Average Daily Rate (VND/room/night)
- RevPAR — Revenue Per Available Room (VND/room/night)
- International visitor count (if available)

### Step 2 — KPI Trend Chart

Show historical trend table:

| Period | Occupancy (%) | ADR (VND/night) | RevPAR (VND/night) | Int'l Visitors |
|---|---|---|---|---|

Note trend direction (improving / declining / stable).

### Step 3 — Property Landscape

```python
from src.db.queries import get_hotel_projects, get_hotel_room_breakdown

with get_session() as s:
    hotels = get_hotel_projects(s, city_name=city_name, district_name=district)
    for hotel in hotels:
        rooms = get_hotel_room_breakdown(s, hotel.id)
```

For each hotel, show:
- Name, brand, operator
- Star rating, hotel type
- Total rooms
- Key amenities (pool, spa, gym, sky bar, conference)
- Notes on positioning

### Step 4 — Room Type Analysis (if single hotel)

For focused hotel analysis, show room breakdown:

| Room Type | Area (m²) | Count | Mix (%) |
|---|---|---|---|
| Standard | 30 | 70 | 47% |
| Deluxe | 35 | 55 | 37% |
| ... | | | |

Highlight the revenue mix implications.

### Step 5 — Thao Dien Submarket Context (if applicable)

When Thu Duc / Thao Dien is in scope:
- 26 total hotels: 7 branded, 19 unbranded
- Branded rate: 2.3–2.9M VND/night
- Unbranded rate: 0.3–1.3M VND/night
- 6 sky bars all in low-rise 4–6F buildings (gap opportunity for high-rise sky bar)
- M Village: 5 properties = dominant branded presence
- Metro Line 1 impact on hotel demand from business travelers

### Step 6 — Competitive Positioning (for Mozac Plan B context)

If Mozac or proposed hotel is mentioned:
- Mozac Plan B: 148 rooms, 4-star, floors 11–18F (625–770m²/floor)
- Benchmark: Amanaki Thao Dien (boutique + Grade B office) and Riverbank Place (Le Méridien + Grade A)
- Target ADR premium vs. existing unbranded hotels
- Mixed-use synergy: office tenants → hotel guests

## Key Metrics Reference

| Metric | Definition | Vietnam Typical Range |
|---|---|---|
| Occupancy | Rooms sold / rooms available | 60–75% (HCMC 2024) |
| ADR | Revenue / rooms sold | 1.5–3M VND/night (4-star) |
| RevPAR | Occupancy × ADR | 1–2.2M VND/night |
| RevPAR = ADR × Occupancy | Math check | Always verify |

## Output Format

```
## HCMC Hotel Market — [Year]-[Half]

### Market KPIs
[Metrics table]

### Trend (Past Periods)
[Trend table]

### Property Landscape
[Hotel list with key specs]

### Room Mix (if single property)
[Room type table]

### Key Insights
[Bullet points: demand drivers, gaps, risks]
```

$ARGUMENTS
