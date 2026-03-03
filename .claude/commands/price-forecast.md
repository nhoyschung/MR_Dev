# /price-forecast — Price Forecast (2-Period Ahead)

Statistical price forecast using Holt's double exponential smoothing.
Projects city-wide or grade-specific prices 1–2 half-year periods forward
with 95% confidence intervals.

## Usage
```
/price-forecast [city] [grade?]
```

**Examples:**
- `/price-forecast HCMC` — City-wide average price forecast
- `/price-forecast Hanoi H-I` — Grade H-I price forecast for Hanoi
- `/price-forecast Binh Duong M-II` — Mid-end II forecast for Binh Duong
- `/price-forecast HCMC all` — Forecast for every grade tier in HCMC

## Instructions

Parse `$ARGUMENTS` to extract:
- `city` — required (supports aliases: HCMC, HCM, Saigon, BD, Ha Noi…)
- `grade` — optional grade code (SL / L / H-I / H-II / M-I / M-II / M-III / A-I / A-II)
            or "all" to run forecasts for every grade

### Step 1 — Resolve city

```python
from src.db.connection import get_session
from src.db.queries import get_city_by_name, resolve_city_name

with get_session() as session:
    city = get_city_by_name(session, city_arg)
    if city is None:
        # Return: "City not found. Available: HCMC, Hanoi, Binh Duong, Da Nang"
```

### Step 2a — City-wide forecast (no grade specified)

```python
from src.reports.price_forecast import forecast_city_price, render_price_forecast

with get_session() as session:
    result = forecast_city_price(session, city_arg, periods_ahead=2)
    if result is None:
        # Return: "Insufficient price history for [city] — need at least 2 periods."
    print(render_price_forecast(result))
```

### Step 2b — Grade-specific forecast

```python
from src.reports.price_forecast import forecast_grade_price, render_price_forecast

with get_session() as session:
    result = forecast_grade_price(
        session, city.name_en, city.id, grade_code, periods_ahead=2
    )
    if result is None:
        # Return: "No price data found for grade [X] in [city]."
    print(render_price_forecast(result))
```

### Step 2c — All grades ("all")

Run `forecast_grade_price` for every grade that has data in the city,
then present results as a consolidated table:

```
| Grade | Last Price | Forecast +1 | Forecast +2 | Trend |
|-------|-----------|-------------|-------------|-------|
| SL    | $9,200    | $9,500      | $9,800      | ↑ +3.3% |
| L     | $6,500    | $6,700      | $6,900      | ↑ +3.1% |
...
```

Followed by the full detailed report for each grade.

## Output Format

```
# Price Forecast — HCMC (City Average)

**Trend:** ↑ 2.8% per period (rising)
**Method:** HOLT
**In-sample RMSE:** $85/m²

## Historical Prices

| Period  | Avg Price (USD/m²) | Projects |
|---------|--------------------|----------|
| 2023-H1 | $3,200             | 18       |
| 2023-H2 | $3,290             | 20       |
| 2024-H1 | $3,380             | 22       |

## Forecast

| Period          | Forecast (USD/m²) | 95% CI Lower | 95% CI Upper |
|-----------------|-------------------|--------------|--------------|
| **2024-H2** *(forecast)* | **$3,475**   | $3,310       | $3,640       |
| **2025-H1** *(forecast)* | **$3,570**   | $3,340       | $3,800       |

## Notes
- Short history (< 4 periods) — forecast uncertainty is high.
```

## Grade Codes Reference

| Code | Segment | Typical Price Range (HCMC) |
|------|---------|---------------------------|
| SL   | Super Luxury | > $10,000/m² |
| L    | Luxury | $6,000–$10,000/m² |
| H-I  | High-End I | $4,000–$6,000/m² |
| H-II | High-End II | $2,500–$4,000/m² |
| M-I  | Mid-End I | $1,800–$2,500/m² |
| M-II | Mid-End II | $1,200–$1,800/m² |
| M-III| Mid-End III | $800–$1,200/m² |
| A-I  | Affordable I | $500–$800/m² |
| A-II | Affordable II | < $500/m² |

## Caveats to Include in Output

Always append:
> *Forecasts are statistical extrapolations based on historical averages.
> They do not account for regulatory changes, macro shocks, new project launches,
> or developer pricing decisions. Use as directional indication only.*

$ARGUMENTS
