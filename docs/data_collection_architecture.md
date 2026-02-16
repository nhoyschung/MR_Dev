# Data Collection & Ingestion System Architecture

## Overview
Automated system for collecting, processing, and ingesting NHO-PD market research reports into the MR-System database.

## System Components

### 1. PDF File Scanner
**Purpose**: Discover new PDF files in monitored directories

**Features**:
- Scan `user_resources/D_colect` for PDF files
- Compare with `source_reports` table to identify new files
- Support multiple watch directories
- Filter by filename patterns (e.g., NHO-PD reports)

**Output**: List of new/unprocessed PDF files

---

### 2. PDF Metadata Extractor
**Purpose**: Extract structured metadata from PDF files

**Metadata Fields**:
```python
{
    "filename": str,              # Original filename
    "file_path": str,             # Absolute path
    "file_size_mb": float,        # File size in MB
    "file_created": datetime,     # File creation timestamp
    "file_modified": datetime,    # Last modified timestamp
    "pdf_pages": int,             # Number of pages
    "pdf_title": str,             # PDF metadata title
    "pdf_author": str,            # PDF metadata author
    "pdf_created": datetime,      # PDF creation date
    "inferred_report_type": str,  # Parsed from filename
    "inferred_city": str,         # Parsed from filename
    "inferred_period": str,       # Parsed from filename (YYYY-H1/H2)
    "inferred_date": date,        # Parsed from filename (YYYYMMDD)
}
```

**Filename Parsing Patterns**:
- `YYYYMMDD_NHO-PD_<Type>_<Details>.pdf`
- `YYYYMMDD_NHO_PD_<City> Market Analysis YYYY.pdf`
- Extract: date, organization, report type, city, year

**Example**:
```
20251117_NHO-PD_2025 HCMC Market Analysis.pdf
→ {
    "inferred_date": "2025-11-17",
    "inferred_report_type": "market_analysis",
    "inferred_city": "Ho Chi Minh City",
    "inferred_period": "2025-H2"
}
```

---

### 3. PDF Text Extraction Service
**Purpose**: Extract text content from PDF files

**Strategy**: Multi-pass extraction for large documents
- **Pass 1**: Overview/Summary sections (pages 1-20)
- **Pass 2**: Mid-document details (pages 21-60)
- **Pass 3**: Deep sections (pages 61+)

**Features**:
- Use PyMuPDF (fitz) for text extraction
- Handle scanned PDFs (OCR fallback if needed)
- Preserve formatting where possible
- Split large extractions into manageable chunks
- Save to `user_resources/D_colect/extracted/`

**Output Files**:
- `<basename>_pass1.txt` (overview)
- `<basename>_pass2.txt` (details)
- `<basename>_pass3.txt` (deep sections)
- `<basename>_full.txt` (complete if small <100 pages)

**Extraction Report**:
```python
{
    "total_pages": int,
    "extracted_pages": int,
    "text_length": int,
    "extraction_time_sec": float,
    "quality_score": float,  # 0-1 based on text density
    "errors": list[str],
}
```

---

### 4. Database Ingestion Manager
**Purpose**: Update database with extracted data and metadata

**Operations**:
1. Create/Update `SourceReport` record
2. Link to `City`, `ReportPeriod` (match or create)
3. Track extraction status
4. Create `DataLineage` records
5. Update related tables (if structured data parsed)

**Status Workflow**:
```
pending → scanning → extracting → extracted → parsing → ingested → error
```

**Database Schema Updates**:
```sql
ALTER TABLE source_reports ADD COLUMN pdf_path TEXT;
ALTER TABLE source_reports ADD COLUMN file_size_mb REAL;
ALTER TABLE source_reports ADD COLUMN extraction_started_at DATETIME;
ALTER TABLE source_reports ADD COLUMN extraction_completed_at DATETIME;
ALTER TABLE source_reports ADD COLUMN extraction_time_sec REAL;
ALTER TABLE source_reports ADD COLUMN quality_score REAL;
```

---

### 5. Ingestion Orchestrator
**Purpose**: Coordinate entire pipeline from PDF → Database

**Workflow**:
```
1. Scan for new PDFs
   ↓
2. Extract metadata
   ↓
3. Create SourceReport record (status: pending)
   ↓
4. Extract text (multi-pass)
   ↓
5. Update SourceReport (status: extracted)
   ↓
6. [Optional] Parse structured data
   ↓
7. Update SourceReport (status: ingested)
   ↓
8. Log completion + metrics
```

**Error Handling**:
- Retry logic (3 attempts with exponential backoff)
- Error status tracking
- Detailed error logs
- Email/notification on failure (optional)

**Concurrency**:
- Process multiple PDFs in parallel (max 3 concurrent)
- Queue-based job management
- Progress tracking per file

---

### 6. File System Watcher
**Purpose**: Monitor directories for new files automatically

**Modes**:
- **Real-time Watch**: Use `watchdog` library to detect new files immediately
- **Scheduled Scan**: Run scanner on schedule (e.g., every hour)

**Triggers**:
- File created event → trigger ingestion
- File modified event → check if already processed
- Ignore temporary files (`.tmp`, `.part`)

**Configuration**:
```yaml
watch_directories:
  - user_resources/D_colect
  - user_resources/incoming
ignore_patterns:
  - "*.tmp"
  - "*.part"
  - "~$*"
scan_interval_minutes: 60
auto_process: true
```

---

### 7. CLI Commands
**Purpose**: Manual control and monitoring

**Commands**:
```bash
# Ingest single PDF
python -m src.collectors.ingest_pdf <file.pdf>

# Scan and ingest all new PDFs
python -m src.collectors.scan_folder

# Start file watcher daemon
python -m src.collectors.watch [--interval 60]

# Show ingestion status
python -m src.collectors.status [--detailed]

# Reprocess existing file
python -m src.collectors.ingest_pdf <file.pdf> --force

# View extraction logs
python -m src.collectors.logs [--last 10]
```

**Flags**:
- `--dry-run`: Show what would be processed without executing
- `--verbose`: Detailed logging
- `--force`: Reprocess even if already ingested
- `--no-db`: Extract only, don't update database

---

## Directory Structure

```
src/
├── collectors/              # NEW: Data collection modules
│   ├── __init__.py
│   ├── pdf_scanner.py       # Scan directories for PDFs
│   ├── pdf_metadata.py      # Extract PDF metadata
│   ├── pdf_extractor.py     # Extract text from PDFs
│   ├── ingestion_manager.py # Database operations
│   ├── orchestrator.py      # Main pipeline coordinator
│   ├── watcher.py           # File system watcher
│   └── cli.py               # CLI commands
│
├── db/
│   └── models.py            # UPDATE: Add new fields to SourceReport
│
└── config.py                # UPDATE: Add collector settings
```

---

## Configuration

**config.py additions**:
```python
# Data collection settings
WATCH_DIRECTORIES = [
    DATA_DIR / "../user_resources/D_colect",
    DATA_DIR / "../user_resources/incoming",
]

EXTRACTED_TEXT_DIR = DATA_DIR / "../user_resources/D_colect/extracted"

# Processing limits
MAX_CONCURRENT_EXTRACTIONS = 3
EXTRACTION_TIMEOUT_MINUTES = 30
MAX_RETRY_ATTEMPTS = 3

# File patterns
PDF_FILENAME_PATTERNS = [
    r"(\d{8})_NHO-?PD_(.+)\.pdf",
    r"(\d{8})_(.+)\.pdf",
]

# Report type keywords
REPORT_TYPE_KEYWORDS = {
    "market_analysis": ["market analysis", "market report"],
    "price_analysis": ["price analysis", "sales price"],
    "developer_analysis": ["developer analysis", "developer report"],
    "land_review": ["land review", "site analysis"],
    "case_study": ["case study"],
    "development_proposal": ["proposal", "development plan"],
}
```

---

## Implementation Phases

### Phase 1: Core Pipeline (Tasks #19-21)
- PDF metadata extractor
- PDF text extraction service
- Ingestion orchestrator
- Database schema updates

### Phase 2: Automation (Task #22)
- File system watcher
- Scheduled scanning
- Auto-trigger on new files

### Phase 3: CLI & Monitoring (Task #23)
- CLI commands
- Status dashboard
- Logging and reporting

### Phase 4: Enhancements (Future)
- Web UI for monitoring
- Email notifications
- Advanced parsing for structured data
- Integration with data-extractor agent

---

## Success Metrics

- **Coverage**: 100% of PDFs tracked in database
- **Automation**: 0 manual steps required for new files
- **Speed**: <5 minutes to process typical report (100 pages)
- **Reliability**: <1% extraction failure rate
- **Observability**: Real-time status dashboard

---

## Security Considerations

- Validate file types before processing
- Sandbox PDF extraction (prevent malicious files)
- Rate limiting on extraction
- Disk space monitoring
- Access control on watch directories
