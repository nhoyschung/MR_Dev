# /project-profile — Project Deep Dive

Generate a comprehensive profile for a single real estate project.

## Usage
```
/project-profile [project name]
```

**Examples:**
- `/project-profile "Masteri Thao Dien"`
- `/project-profile "Vinhomes Grand Park"`
- `/project-profile "The Felix"`

## Instructions

Query the database for the specified project and produce a detailed profile:

### 1. Project Identity
- Name, developer, location (district/city)
- Project type, status, grade classification
- Total units, launch date, completion date

### 2. Pricing
- Current price (USD/m2 and VND/m2)
- Grade classification and where it sits in the grade range
- Price history (if multiple periods available)
- Price change factors

### 3. Developer Context
- Developer name, stock code, HQ
- Other projects by the same developer
- Developer's typical price segment

### 4. Location Context
- District overview
- Other projects in the same district
- District average price vs this project's price

### 5. Competitive Position
- Projects in the same grade
- Price comparison with grade peers
- Key differentiators

### 6. Sales & Supply (if available)
- Sales status (units launched, sold, available)
- Absorption rate
- Inventory status

## Quick Render (Preferred)

Use the pre-built renderer for a complete template-based report:
```python
from src.db.connection import get_session
from src.reports.project_profile import render_project_profile

with get_session() as s:
    report = render_project_profile(s, project_name)
    # report is a complete markdown string
```

Parse project name from `$ARGUMENTS`. Supports exact or substring match.

## Manual Queries (For Custom Analysis)

```python
from src.db.connection import get_session
from src.db.models import Project, PriceRecord, Developer
from src.db.queries import (
    get_latest_price, get_price_history, list_projects_by_grade,
    list_projects_by_developer, get_grade_for_price,
)
```

## Output Format
Structured markdown with headers, tables, and key metrics highlighted.
After rendering, review the output and add any additional insights or commentary as needed.

$ARGUMENTS
