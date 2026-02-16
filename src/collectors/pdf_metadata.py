"""PDF metadata extraction module."""

import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF

from dataclasses import dataclass


@dataclass
class PDFMetadata:
    """Structured metadata extracted from PDF file."""
    # File metadata
    filename: str
    file_path: str
    file_size_mb: float
    file_created: datetime
    file_modified: datetime

    # PDF properties
    pdf_pages: int
    pdf_title: Optional[str] = None
    pdf_author: Optional[str] = None
    pdf_subject: Optional[str] = None
    pdf_creator: Optional[str] = None
    pdf_created: Optional[datetime] = None

    # Inferred from filename
    inferred_date: Optional[date] = None
    inferred_report_type: Optional[str] = None
    inferred_city: Optional[str] = None
    inferred_period: Optional[str] = None

    # Additional
    extraction_timestamp: datetime = None

    def __post_init__(self):
        if self.extraction_timestamp is None:
            self.extraction_timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size_mb": self.file_size_mb,
            "file_created": self.file_created.isoformat() if self.file_created else None,
            "file_modified": self.file_modified.isoformat() if self.file_modified else None,
            "pdf_pages": self.pdf_pages,
            "pdf_title": self.pdf_title,
            "pdf_author": self.pdf_author,
            "pdf_subject": self.pdf_subject,
            "pdf_creator": self.pdf_creator,
            "pdf_created": self.pdf_created.isoformat() if self.pdf_created else None,
            "inferred_date": self.inferred_date.isoformat() if self.inferred_date else None,
            "inferred_report_type": self.inferred_report_type,
            "inferred_city": self.inferred_city,
            "inferred_period": self.inferred_period,
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
        }


# Report type keywords for classification
REPORT_TYPE_KEYWORDS = {
    "market_analysis": ["market analysis", "market report", "market overview"],
    "price_analysis": ["price analysis", "sales price", "pricing"],
    "developer_analysis": ["developer analysis", "developer report"],
    "land_review": ["land review", "site analysis", "land analysis"],
    "case_study": ["case study"],
    "development_proposal": ["proposal", "development plan", "development proposal"],
    "supply_analysis": ["supply", "inventory"],
}

# City name mappings
CITY_MAPPINGS = {
    "hcmc": "Ho Chi Minh City",
    "ho chi minh": "Ho Chi Minh City",
    "saigon": "Ho Chi Minh City",
    "hanoi": "Hanoi",
    "ha noi": "Hanoi",
    "binh duong": "Binh Duong",
    "hai phong": "Hai Phong",
    "bac ninh": "Bac Ninh",
    "dong nai": "Dong Nai",
    "da nang": "Da Nang",
}


def extract_pdf_metadata(pdf_path: str | Path) -> PDFMetadata:
    """Extract comprehensive metadata from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        PDFMetadata object with all extracted information

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If file is not a valid PDF
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_path.suffix.lower() == ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")

    # Extract file system metadata
    stat = pdf_path.stat()
    file_size_mb = stat.st_size / (1024 * 1024)
    file_created = datetime.fromtimestamp(stat.st_ctime)
    file_modified = datetime.fromtimestamp(stat.st_mtime)

    # Extract PDF properties
    doc = fitz.open(pdf_path)
    pdf_pages = len(doc)
    pdf_meta = doc.metadata

    pdf_title = pdf_meta.get("title") or None
    pdf_author = pdf_meta.get("author") or None
    pdf_subject = pdf_meta.get("subject") or None
    pdf_creator = pdf_meta.get("creator") or None

    # Parse PDF creation date (format: D:20240515120000)
    pdf_created = None
    if pdf_meta.get("creationDate"):
        pdf_created = _parse_pdf_date(pdf_meta["creationDate"])

    doc.close()

    # Parse filename for additional metadata
    filename = pdf_path.name
    inferred_date = _parse_date_from_filename(filename)
    inferred_report_type = _infer_report_type(filename)
    inferred_city = _infer_city(filename)
    inferred_period = _infer_period(filename, inferred_date)

    return PDFMetadata(
        filename=filename,
        file_path=str(pdf_path.absolute()),
        file_size_mb=round(file_size_mb, 2),
        file_created=file_created,
        file_modified=file_modified,
        pdf_pages=pdf_pages,
        pdf_title=pdf_title,
        pdf_author=pdf_author,
        pdf_subject=pdf_subject,
        pdf_creator=pdf_creator,
        pdf_created=pdf_created,
        inferred_date=inferred_date,
        inferred_report_type=inferred_report_type,
        inferred_city=inferred_city,
        inferred_period=inferred_period,
    )


def _parse_pdf_date(pdf_date_str: str) -> Optional[datetime]:
    """Parse PDF date string (format: D:20240515120000+07'00')."""
    try:
        # Remove 'D:' prefix
        if pdf_date_str.startswith("D:"):
            pdf_date_str = pdf_date_str[2:]

        # Extract date/time part (before timezone)
        date_part = pdf_date_str.split("+")[0].split("-")[0]

        # Parse YYYYMMDDHHMMSS
        if len(date_part) >= 14:
            return datetime.strptime(date_part[:14], "%Y%m%d%H%M%S")
        elif len(date_part) >= 8:
            return datetime.strptime(date_part[:8], "%Y%m%d")

    except Exception:
        pass

    return None


def _parse_date_from_filename(filename: str) -> Optional[date]:
    """Parse date from filename (format: YYYYMMDD_...).

    Args:
        filename: PDF filename

    Returns:
        date object or None if no date found
    """
    # Pattern: YYYYMMDD at start of filename
    match = re.match(r"^(\d{8})", filename)
    if match:
        date_str = match.group(1)
        try:
            return datetime.strptime(date_str, "%Y%m%d").date()
        except ValueError:
            pass

    return None


def _infer_report_type(filename: str) -> Optional[str]:
    """Infer report type from filename.

    Args:
        filename: PDF filename

    Returns:
        Report type string or None
    """
    filename_lower = filename.lower()

    for report_type, keywords in REPORT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return report_type

    return None


def _infer_city(filename: str) -> Optional[str]:
    """Infer city from filename.

    Args:
        filename: PDF filename

    Returns:
        Standardized city name or None
    """
    filename_lower = filename.lower()

    for key, city_name in CITY_MAPPINGS.items():
        if key in filename_lower:
            return city_name

    return None


def _infer_period(filename: str, file_date: Optional[date] = None) -> Optional[str]:
    """Infer report period from filename or date.

    Args:
        filename: PDF filename
        file_date: Parsed date from filename

    Returns:
        Period string (YYYY-H1 or YYYY-H2) or None
    """
    filename_lower = filename.lower()

    # Look for explicit year mentions
    year_match = re.search(r"(20\d{2})", filename)
    if year_match:
        year = year_match.group(1)

        # Check for half indicators
        if any(x in filename_lower for x in ["h1", "1h", "first half", "jan-jun"]):
            return f"{year}-H1"
        elif any(x in filename_lower for x in ["h2", "2h", "second half", "jul-dec"]):
            return f"{year}-H2"

        # Infer from date if available
        if file_date and str(file_date.year) == year:
            half = "H1" if file_date.month <= 6 else "H2"
            return f"{year}-{half}"

        # Default to H2 if no indicator
        return f"{year}-H2"

    # Fallback to date if no year in filename
    if file_date:
        year = file_date.year
        half = "H1" if file_date.month <= 6 else "H2"
        return f"{year}-{half}"

    return None


def batch_extract_metadata(pdf_paths: list[str | Path]) -> list[PDFMetadata]:
    """Extract metadata from multiple PDFs.

    Args:
        pdf_paths: List of PDF file paths

    Returns:
        List of PDFMetadata objects
    """
    results = []
    for pdf_path in pdf_paths:
        try:
            metadata = extract_pdf_metadata(pdf_path)
            results.append(metadata)
        except Exception as e:
            print(f"Error extracting metadata from {pdf_path}: {e}")

    return results
