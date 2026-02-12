# /vn-market-briefing — Vietnam Market Briefing

Generate a comprehensive market overview for a city and time period.

## Usage
```
/vn-market-briefing [city] [period]
```

**Examples:**
- `/vn-market-briefing HCMC 2024-H1`
- `/vn-market-briefing Hanoi 2024-H2`
- `/vn-market-briefing "Binh Duong" 2025-H1`

## Instructions

Query the MR-System database and generate a market briefing with these sections:

### 1. Market Snapshot
- Total projects tracked in the city
- Active new launches in the period
- Average price by segment (USD/m2)
- Overall absorption rate

### 2. Grade Distribution
Show the distribution of projects across the grading system (SL/L/H-I/H-II/M-I/M-II/M-III/A-I/A-II) with counts and average prices.

### 3. District Highlights
- Top 5 districts by average price
- Top 5 districts by new supply
- Districts with highest absorption rates

### 4. Price Trends
- Average price changes from previous period
- Notable price movements (projects with >10% change)
- Grade migration (projects that moved up/down grades)

### 5. Supply Pipeline
- New supply entering the market
- Projects under construction
- Upcoming launches

### 6. Key Takeaways
3-5 bullet points summarizing the market state for investors and developers.

## Quick Render (Preferred)

Use the pre-built renderer for a complete template-based report:
```python
from src.db.connection import get_session
from src.reports.market_briefing import render_market_briefing

with get_session() as s:
    report = render_market_briefing(s, city_name, year, half)
    # report is a complete markdown string
```

Parse arguments from `$ARGUMENTS`: e.g. "HCMC 2024-H1" → city_name="HCMC", year=2024, half="H1".
City aliases are supported: HCMC, HCM, Saigon, BD, Ha Noi.

## Manual Queries (For Custom Analysis)

Use the helpers in `src/db/queries.py`:
```python
from src.db.connection import get_session
from src.db.queries import (
    get_city_by_name, list_projects_by_city, avg_price_by_district,
    get_market_summary, count_projects_by_city,
)
```

## Output Format
Markdown report with tables and bullet points. Include the period and data source counts at the top.
After rendering, review the output and add any additional insights or commentary as needed.

$ARGUMENTS
