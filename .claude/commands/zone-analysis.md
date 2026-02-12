# /zone-analysis — District/Zone Analysis

Supply-demand analysis for a specific district or zone.

## Usage
```
/zone-analysis [district] [city]
```

**Examples:**
- `/zone-analysis "District 2" HCMC`
- `/zone-analysis "Thuan An" "Binh Duong"`
- `/zone-analysis "Cau Giay" Hanoi`

## Instructions

### 1. Zone Overview
- District name (EN/VI), city, district type (urban/suburban)
- Number of tracked projects
- Active projects (selling/under-construction)

### 2. Supply Analysis
- Total inventory in the zone
- New supply for the current period
- Remaining inventory
- Supply pipeline (planned projects)

### 3. Price Landscape
- Average price (USD/m2)
- Price range (min-max)
- Grade distribution of projects in the zone
- Comparison to city average

### 4. Project Roster
Table of all projects in the district:

| Project | Developer | Units | Price (USD/m2) | Grade | Status |
|---------|-----------|-------|----------------|-------|--------|

### 5. Absorption & Demand
- Absorption rate for the zone
- Sold units vs available units
- Demand indicators

### 6. Investment Outlook
- Is the zone over-supplied or under-supplied?
- Price trajectory
- Key opportunities and risks

## Database Access

```python
from src.db.connection import get_session
from src.db.queries import (
    get_city_by_name, get_district_by_name, get_district_supply,
    get_district_metrics, avg_price_by_district,
)
from src.db.models import Project, District
```

City aliases supported: HCMC, HCM, Saigon, BD, Ha Noi, etc.

$ARGUMENTS
