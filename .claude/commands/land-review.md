---
name: land-review
description: /land-review — Land Development Feasibility Analysis
tags:
  - market-research
  - land-analysis
  - feasibility
---

# Task: Generate Land Review & Site Analysis Report

You will generate a comprehensive land development feasibility report using the MR-System's land review automation module.

## Parameters

Parse the user's input to extract the following land site information:

### Required Parameters:
- **city**: City name (e.g., "Ho Chi Minh City", "Hanoi", "Binh Duong")
- **land_area_ha**: Land area in hectares (numeric value)

### Optional Parameters:
- **district**: District name (e.g., "District 2", "Thu Duc", "Dong Nai")
- **ward**: Ward/commune name
- **latitude**: Site latitude (decimal degrees)
- **longitude**: Site longitude (decimal degrees)
- **land_use**: Land use designation (e.g., "residential", "commercial", "mixed-use")
- **development_type**: Intended development type (e.g., "apartment", "mixed-use", "townhouse")
- **target_segment**: Target market segment or grade (e.g., "M-I", "H-I", "Luxury", "Mid-Range")
- **transportation**: Transportation/accessibility notes (string)
- **landmarks**: List of nearby landmarks (array of strings)
- **strengths**: Site-specific strengths (array of strings)
- **weaknesses**: Site-specific weaknesses (array of strings)

## Instructions

1. **Parse Input**: Extract land site parameters from the user's natural language input or structured data.

2. **Build Land Input Dictionary**: Create a Python dictionary with all provided parameters:

```python
land_input = {
    "city": "Ho Chi Minh City",  # Required
    "land_area_ha": 35.0,        # Required
    "district": "District 2",    # Optional
    "ward": "Thao Dien",         # Optional
    "latitude": 10.8042,         # Optional but highly recommended
    "longitude": 106.7394,       # Optional but highly recommended
    "land_use": "residential",   # Optional
    "development_type": "mixed-use",  # Optional
    "target_segment": "M-I",     # Optional
    # Additional optional fields:
    "transportation": "5 min to Thu Thiem Bridge, 15 min to CBD",
    "landmarks": ["Thu Thiem New Urban Area", "Metro Line 1"],
    "strengths": ["Prime riverside location", "Adjacent to business district"],
    "weaknesses": ["Limited infrastructure", "Flood risk during monsoon"],
}
```

3. **Generate Report**: Use the land review module to generate the comprehensive analysis:

```python
from src.db.connection import get_session
from src.reports.land_review import generate_land_review_report

# Generate report
with get_session() as session:
    report = generate_land_review_report(session, land_input)

# Save to file
output_file = f"land_review_{land_input['city'].replace(' ', '_')}_{land_input.get('district', 'Unknown').replace(' ', '_')}.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(report)
```

4. **Present Results**: Display the report summary to the user and save the full report to a markdown file.

## Report Sections

The generated report includes:

1. **Executive Summary** - Key highlights and development potential
2. **Location Analysis** - Geographic overview, accessibility, strengths/weaknesses
3. **Market Analysis** - Supply/demand trends, pricing benchmarks
4. **Competitive Landscape** - Nearby competitor projects (within 5km radius)
5. **SWOT Analysis** - Comprehensive strengths, weaknesses, opportunities, threats
6. **Development Recommendations** - Product mix, pricing strategy, timeline
7. **Risk Assessment** - Market, development, and regulatory risks
8. **Financial Feasibility** - Preliminary GDV and profitability estimates
9. **Implementation Roadmap** - Step-by-step development plan
10. **Conclusion** - Viability assessment and recommendations

## Examples

### Example 1: Full Specification

```
User: "Analyze a 35 hectare land site in District 2, Ho Chi Minh City at coordinates 10.8042, 106.7394.
Target mid-range segment (M-I grade). Strengths: prime location, near Thu Thiem. Weaknesses: flood risk."
```

### Example 2: Minimal Input

```
User: "Land review for 20ha site in Hanoi, Tay Ho district"
```

### Example 3: Structured Data

```
User: "/land-review
City: Binh Duong
District: Thuan An
Land area: 45 hectares
Target segment: Affordable (A-I)
Strengths: Adjacent to industrial zones, low land cost
Weaknesses: Limited infrastructure, far from city center"
```

## Output Format

1. Display a summary showing:
   - Land location and size
   - Target segment
   - Number of competitors found
   - Estimated development scale
   - Viability assessment (🟢 Highly Viable / 🟡 Moderately Viable / 🔴 Requires Further Study)

2. Save full detailed report to markdown file

3. Provide the file path to the user

## Important Notes

- **Coordinates Highly Recommended**: Providing latitude/longitude enables competitor proximity analysis and significantly improves report quality
- **Market Data Dependency**: Report quality depends on available market data in the database for the specified city/district
- **Customization**: Users can provide site-specific strengths/weaknesses to enhance the SWOT analysis
- **Preliminary Analysis**: This is an automated preliminary feasibility study; detailed financial modeling and site surveys are still required

## Error Handling

- If city not found in database: Provide error message with list of available cities
- If no market data available: Report will note data gaps and recommend primary research
- If no coordinates provided: Report will skip proximity-based competitor analysis
- If invalid parameters: Prompt user to provide required fields (city, land_area_ha)

---

After generating the report, ask the user if they want to:
1. Refine the analysis with additional parameters
2. Generate a comparison report for alternative sites
3. Export data for detailed financial modeling
