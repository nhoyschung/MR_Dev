# /office-market — Office Market Analysis

Analyze the HCMC office market: building profiles, rent benchmarks, grade comparison, and market context.

## Usage
```
/office-market [city] [year] [half] [optional: grade | building name | district]
```

**Examples:**
- `/office-market hcmc 2024 H2` — Citywide office market overview
- `/office-market hcmc 2023 H1 "Grade A"` — Grade A buildings with rents
- `/office-market hcmc 2024 H2 "The Hallmark"` — Single building deep dive
- `/office-market hcmc 2024 H2 "District 1"` — CBD office landscape

## Instructions

Parse arguments from `$ARGUMENTS`. Default city = "Ho Chi Minh City", default period = most recent available.

### Step 1 — Market Overview

Query the office market summary:

```python
from src.db.connection import get_session
from src.db.queries import get_office_market_summary, get_office_rent_comparison

with get_session() as s:
    summary = get_office_market_summary(s, city_name, year, half)
    rent_table = get_office_rent_comparison(s, city_name, year, half)
```

Report:
- Total stock (NLA m²) broken down by Grade A / B / C
- Number of buildings (total and Grade A)
- Average rent by grade (USD/m²/month)
- Average occupancy by grade (%)
- Net absorption and new supply

### Step 2 — Building Rent Benchmark Table

Render a comparison table of all buildings with leasing data for the period:

| Building | Grade | Rent ($/m²/mo) | Mgmt Fee | Occupancy | Certification |
|---|---|---|---|---|---|

Sort by rent descending. Highlight the highest and lowest.

### Step 3 — Grade A Deep Dive

For Grade A buildings:
```python
from src.db.queries import get_office_projects, get_office_leasing_history

with get_session() as s:
    grade_a = get_office_projects(s, city_name=city_name, grade="A")
    for proj in grade_a:
        history = get_office_leasing_history(s, proj.id)
```

Show key specs: floors, NLA, ceiling height, raised floor, certifications.

### Step 4 — Thao Dien / D2 Submarket Spotlight

If district = Thu Duc or D2 context is relevant:
- Note The Hallmark as the only Grade A asset in the submarket
- Worc@Q2 as the highest Grade B+ competitor ($23.5-30/m²)
- Gap analysis vs. CBD Grade A ($55-74/m²)
- Metro Line 1 accessibility advantage

### Step 5 — Market Intelligence

Synthesize key insights:
1. Supply balance: new supply vs. absorption
2. Rent trajectory: compare with previous period if available
3. Demand drivers: ICT (35%), Finance (14%), Manufacturing (13%) per sector
4. Foreign company dominance (82% of tenants)
5. Grade migration: B tenants upgrading to A vs. C tenants churning

## Output Format

Structured markdown:
```
## HCMC Office Market — [Year]-[Half]

### Market Overview
[Summary table]

### Rent Benchmark
[Comparison table ordered by rent]

### Grade A Deep Dive
[Spec table + leasing data]

### Key Insights
[Bullet points]
```

$ARGUMENTS
