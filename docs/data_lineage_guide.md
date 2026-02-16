# Data Lineage Tracking Guide

## Overview

The Data Lineage Tracking System provides full traceability for all data extracted from source reports into the MR-System database. It enables:

- **Source Attribution**: Know exactly which PDF report each record came from
- **Quality Monitoring**: Track confidence scores for data quality assessment
- **Audit Trails**: Complete history of data extraction activities
- **Data Validation**: Verify extracted data against source documents

## System Architecture

### Database Tables

**source_reports**
- Tracks PDF source documents
- Fields: filename, report_type, city_id, period_id, page_count, status

**data_lineage**
- Links database records to source reports
- Fields: table_name, record_id, source_report_id, page_number, confidence_score, extracted_at

### Relationships

```
SourceReport (1) ←→ (many) DataLineage
DataLineage.source_report_id → SourceReport.id
DataLineage.table_name + record_id → Any table record
```

## Usage Examples

### 1. Track New Data Extraction

```python
from src.utils.lineage_tracker import track_lineage, register_source_report

# Register a new source report
report = register_source_report(
    session,
    filename="hcmc_2024_h1.txt",
    report_type="market_analysis",
    city_id=1,
    period_id=5,
    page_count=150
)

# Track lineage for extracted project
lineage = track_lineage(
    session,
    table_name="projects",
    record_id=42,
    source_report_id=report.id,
    page_number=87,
    confidence_score=0.95
)

session.commit()
```

### 2. Query Record Lineage

```python
from src.reports.data_lineage import get_record_lineage

# Find source of a specific project
lineage = get_record_lineage(session, "projects", 42)

print(f"Source: {lineage['source_report']}")
print(f"Type: {lineage['report_type']}")
print(f"Page: {lineage['page_number']}")
print(f"Confidence: {lineage['confidence_score']}")
print(f"Extracted: {lineage['extracted_at']}")
```

### 3. Analyze Source Report Impact

```python
from src.reports.data_lineage import get_source_impact

impact = get_source_impact(session, source_report_id=5)

print(f"Report: {impact['source_report']}")
print(f"Total records: {impact['total_records']}")
print("\nTable breakdown:")
for table in impact['table_breakdown']:
    print(f"  {table['table']}: {table['count']} records")
```

### 4. Monitor Data Quality

```python
from src.reports.data_lineage import get_quality_metrics
from src.utils.lineage_tracker import find_low_confidence_records

# Overall quality
metrics = get_quality_metrics(session)
print(f"Average confidence: {metrics['avg_confidence']:.2f}")
print(f"High quality (≥0.8): {metrics['high_confidence']} records")
print(f"Low quality (<0.5): {metrics['low_confidence']} records")

# Find records needing review
low_conf = find_low_confidence_records(session, threshold=0.5)
for lineage in low_conf[:10]:
    print(f"{lineage.table_name}:{lineage.record_id} - {lineage.confidence_score:.2f}")
```

### 5. Generate Lineage Report

```python
from src.reports.data_lineage import render_lineage_report

# Generate comprehensive lineage report
report = render_lineage_report(session)

# Save to file
with open("lineage_report.md", "w", encoding="utf-8") as f:
    f.write(report)
```

### 6. Validate System Integrity

```python
from src.utils.lineage_tracker import validate_lineage_integrity

validation = validate_lineage_integrity(session)

if validation['is_valid']:
    print("✓ Lineage system integrity validated")
else:
    print("✗ Issues found:")
    for issue in validation['issues']:
        print(f"  - {issue}")
```

## Confidence Scoring

### Score Ranges

- **0.9-1.0**: Highly confident - Data extracted from clear, structured text
- **0.7-0.9**: Confident - Data extracted with minor ambiguity
- **0.5-0.7**: Moderate - Data extracted with some interpretation
- **0.3-0.5**: Low - Data extracted with significant uncertainty
- **0.0-0.3**: Very low - Data may require manual verification

### Best Practices

1. **Set appropriate scores** during extraction based on:
   - Text clarity and structure
   - Presence of validation data (cross-references)
   - Extraction method reliability

2. **Review low-confidence records** periodically:
   ```python
   low_conf = find_low_confidence_records(session, threshold=0.6)
   # Manual review and update
   ```

3. **Update scores** after verification:
   ```python
   from src.utils.lineage_tracker import update_confidence
   update_confidence(session, "projects", 42, new_confidence=0.95)
   ```

## Workflow Integration

### Data Extraction Pipeline

```python
# 1. Register source report
report = register_source_report(session, filename, report_type)

# 2. Extract data from PDF
extracted_data = extract_from_pdf(filename)

# 3. Insert into database + track lineage
for item in extracted_data:
    # Insert record
    project = Project(**item)
    session.add(project)
    session.flush()  # Get ID

    # Track lineage
    track_lineage(
        session,
        table_name="projects",
        record_id=project.id,
        source_report_id=report.id,
        page_number=item['_meta']['page'],
        confidence_score=item['_meta'].get('confidence', 0.7)
    )

# 4. Mark report as ingested
mark_source_ingested(session, report.id)
session.commit()
```

## Maintenance

### Regular Checks

**Weekly:**
- Run `validate_lineage_integrity()` to check for issues
- Review low-confidence records (<0.5)
- Update confidence scores after manual verification

**Monthly:**
- Generate full lineage report for audit
- Review unused source reports
- Archive old lineage data if needed

### Data Cleanup

```python
# Find source reports with no lineage (may indicate failed extraction)
unused = session.query(SourceReport).filter(
    ~SourceReport.id.in_(session.query(DataLineage.source_report_id)),
    SourceReport.status == "ingested"
).all()

for report in unused:
    print(f"Unused: {report.filename} - investigate extraction")
```

## Troubleshooting

### Issue: Missing Lineage Records

**Symptom:** Records in database but no lineage entry

**Solution:**
1. Check if extraction script includes `track_lineage()` call
2. Verify session.commit() after lineage tracking
3. Re-run extraction for affected records

### Issue: Low Average Confidence

**Symptom:** System-wide confidence <0.6

**Solution:**
1. Review extraction algorithms
2. Improve PDF text parsing quality
3. Add validation steps during extraction
4. Manual review and update of low-confidence records

### Issue: Orphaned Lineage Records

**Symptom:** Lineage references non-existent source reports

**Solution:**
```python
# Clean up orphaned lineage
orphaned = session.query(DataLineage).filter(
    ~DataLineage.source_report_id.in_(session.query(SourceReport.id))
).all()

for lineage in orphaned:
    session.delete(lineage)
session.commit()
```

## API Reference

### Core Functions

**lineage_tracker.py:**
- `track_lineage()` - Create lineage record
- `update_confidence()` - Update confidence score
- `find_records_from_source()` - Get records from source
- `find_low_confidence_records()` - Find records needing review
- `register_source_report()` - Register new source
- `mark_source_ingested()` - Mark source as processed
- `get_lineage_statistics()` - Get system stats
- `validate_lineage_integrity()` - Validate system

**data_lineage.py:**
- `get_record_lineage()` - Get lineage for specific record
- `get_source_impact()` - Analyze source report impact
- `get_quality_metrics()` - Get quality statistics
- `get_extraction_timeline()` - Get timeline data
- `get_table_coverage()` - Get coverage by table
- `render_lineage_report()` - Generate full report

## Future Enhancements

- **Version Tracking**: Track updates to existing records
- **Data Lineage Graph**: Visual graph of data flow
- **Automated Quality Checks**: Real-time quality monitoring
- **Change Detection**: Alert on unexpected data changes
- **Lineage API**: REST API for lineage queries
