# /price-check — Price Lookup with Grade Context

Quick price lookup for a project with grade classification and trend context.

## Usage
```
/price-check [project name or price] [city]
```

**Examples:**
- `/price-check "Masteri Thao Dien"` — Look up project's current price and grade
- `/price-check 3500 HCMC` — What grade is $3,500/m2 in HCMC?
- `/price-check "Vinhomes Grand Park"` — Price + grade + trend

## Instructions

### If project name provided:
1. Look up the project in the database
2. Get latest price record (USD/m2 and VND/m2)
3. Determine grade classification based on city's grade definitions
4. Show where the price sits within the grade range (low/mid/high)
5. Show price history if available
6. Compare to district average and grade average

### If raw price provided:
1. Determine the grade for that price in the specified city
2. Show the grade range (min-max)
3. List example projects in the same grade
4. Show how close the price is to grade boundaries

### Output Format

```
Project: Masteri Thao Dien
City: HCMC | District: District 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Price: $4,200/m2 (105M VND/m2)
Grade: H-I (High-End I)
Range: $4,000 - $6,000/m2
Position: ▓▓░░░░░░░░ Low end of grade

Grade Peers: d'Edge Thao Dien ($4,800), Masteri An Phu ($4,000)
District Avg: $3,800/m2

Trend: — (single period data)
```

## Database Access

```python
from src.db.connection import get_session
from src.db.queries import (
    get_latest_price, get_price_history, get_grade_for_price,
    get_city_by_name, list_projects_by_grade, resolve_city_name,
)
```

City aliases supported: HCMC, HCM, Saigon, BD, Ha Noi, etc.

For project lookup, use substring matching:
```python
from sqlalchemy import select
from src.db.models import Project
project = session.execute(
    select(Project).where(Project.name.ilike(f"%{name}%")).limit(1)
).scalar_one_or_none()
```

$ARGUMENTS
