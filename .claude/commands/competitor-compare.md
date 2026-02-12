# /competitor-compare — Project Comparison

Side-by-side comparison of 2-3 real estate projects using the 11-dimension framework.

## Usage
```
/competitor-compare [project1] vs [project2] [vs project3]
```

**Examples:**
- `/competitor-compare "Masteri Thao Dien" vs "Vista Verde"`
- `/competitor-compare "The Felix" vs "Happy One Morri" vs "Picity Sky Park"`

## Instructions

Use the **competitor-benchmarker** agent approach to compare the specified projects:

### 1. Load Project Data
Query the database for each project's full profile including prices, developer, location, and facilities.

### 2. Comparison Table
Create a side-by-side table:

| Attribute | Project A | Project B |
|-----------|-----------|-----------|
| Location | District, City | District, City |
| Developer | Name | Name |
| Type | apartment/mixed-use | apartment/mixed-use |
| Total Units | N | N |
| Price (USD/m2) | $X | $Y |
| Grade | X-X | Y-Y |
| Status | selling/completed | selling/completed |

### 3. 11-Dimension Scoring
Score each project on: Location, Transportation, Surroundings, Design, Facilities, Unit Layout, Pricing, Developer Brand, Payment Terms, Legal Status, Management.

### 4. Strengths & Weaknesses
For each project, identify top 3 strengths and weaknesses.

### 5. Price-Value Assessment
- Which project offers better value for its price?
- Price premium/discount relative to quality scores

### 6. Recommendation
- Best for investors
- Best for end-users
- Best value overall

## Database Access

```python
from src.db.connection import get_session
from src.db.models import Project, PriceRecord
from src.db.queries import get_latest_price, list_projects_by_grade
```

$ARGUMENTS
