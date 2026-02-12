# /db-query — Direct Database Query

Execute queries against the MR-System database and return formatted results.

## Usage
```
/db-query [natural language query]
```

**Examples:**
- `/db-query How many projects are in each city?`
- `/db-query List all luxury projects in HCMC`
- `/db-query What is the average price in District 2?`
- `/db-query Show all Vinhomes projects with prices`
- `/db-query Which districts have absorption rate above 80%?`

## Instructions

1. Parse the natural language query
2. Translate it into SQLAlchemy queries using the MR-System models
3. Execute the query against `data/mr_system.db`
4. Format results as a clean markdown table

## Database Schema Reference

### Key Tables
- `cities` — id, name_en, name_vi, region
- `districts` — id, city_id, name_en, name_vi, district_type
- `projects` — id, name, developer_id, district_id, total_units, project_type, status, grade_primary
- `developers` — id, name_en, stock_code, hq_city_id
- `price_records` — id, project_id, period_id, price_usd_per_m2, price_vnd_per_m2
- `grade_definitions` — id, city_id, grade_code, min_price_usd, max_price_usd, segment
- `report_periods` — id, year, half
- `supply_records` — id, project_id, period_id, total_inventory, new_supply, sold_units, absorption_rate_pct
- `district_metrics` — id, district_id, period_id, metric_type, value_numeric

### Common Joins
- Project → District → City (location hierarchy)
- Project → Developer (who built it)
- Project → PriceRecord → ReportPeriod (pricing over time)
- Project → SupplyRecord (inventory data)

## Database Access

```python
from src.db.connection import get_session
from src.db.models import *
from sqlalchemy import select, func

session = get_session()
# Execute queries...
session.close()
```

## Output Format
- Always show results in a markdown table
- Include the generated SQLAlchemy query for transparency
- Note the total number of results
- If the query returns no results, suggest alternative queries

$ARGUMENTS
