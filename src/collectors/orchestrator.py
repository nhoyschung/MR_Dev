"""Ingestion orchestrator for PDF collection pipeline."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.connection import get_session
from src.db.models import SourceReport, City, ReportPeriod
from src.collectors.pdf_metadata import extract_pdf_metadata, PDFMetadata
from src.collectors.pdf_extractor import PDFExtractor, ExtractionResult
from src.config import DATA_DIR


class IngestionOrchestrator:
    """Orchestrate PDF ingestion from scanning to database update."""

    def __init__(
        self,
        watch_dir: str | Path,
        extracted_text_dir: str | Path | None = None,
    ):
        """Initialize orchestrator.

        Args:
            watch_dir: Directory to scan for PDF files
            extracted_text_dir: Directory to save extracted text
                (defaults to watch_dir/extracted)
        """
        self.watch_dir = Path(watch_dir)
        if extracted_text_dir is None:
            extracted_text_dir = self.watch_dir / "extracted"
        self.extracted_text_dir = Path(extracted_text_dir)

        self.extractor = PDFExtractor(self.extracted_text_dir)

    def scan_for_new_pdfs(self, session: Session) -> list[Path]:
        """Scan directory for PDFs not yet in database.

        Args:
            session: Database session

        Returns:
            List of Path objects for new PDF files
        """
        # Get all PDFs in watch directory
        all_pdfs = list(self.watch_dir.glob("*.pdf"))

        # Get existing filenames from database
        stmt = select(SourceReport.filename)
        existing_filenames = set(session.execute(stmt).scalars().all())

        # Filter to new files only
        new_pdfs = [
            pdf for pdf in all_pdfs
            if pdf.name not in existing_filenames
        ]

        return new_pdfs

    def ingest_pdf(
        self,
        pdf_path: str | Path,
        session: Session,
        force: bool = False,
    ) -> SourceReport:
        """Ingest a single PDF through the complete pipeline.

        Args:
            pdf_path: Path to PDF file
            session: Database session
            force: If True, reprocess even if already exists

        Returns:
            SourceReport object

        Raises:
            ValueError: If file already exists and force=False
        """
        pdf_path = Path(pdf_path)

        # Check if already exists
        existing = session.execute(
            select(SourceReport).where(SourceReport.filename == pdf_path.name)
        ).scalar_one_or_none()

        if existing and not force:
            raise ValueError(f"PDF already ingested: {pdf_path.name}. Use force=True to reprocess.")

        # Step 1: Extract metadata
        print(f"[METADATA] Extracting metadata: {pdf_path.name}")
        metadata = extract_pdf_metadata(pdf_path)

        # Step 2: Create or update SourceReport record
        if existing:
            report = existing
            report.status = "extracting"
        else:
            report = self._create_source_report(metadata, session)

        report.extraction_started_at = datetime.now(timezone.utc)
        session.commit()

        # Step 3: Extract text
        print(f"[EXTRACT] Extracting text ({metadata.pdf_pages} pages)...")
        try:
            extraction_result = self.extractor.extract_text(
                pdf_path,
                strategy="auto",
                base_name=pdf_path.stem,
            )

            # Step 4: Update report with extraction results
            report.status = "extracted"
            report.extraction_completed_at = datetime.now(timezone.utc)
            report.extraction_time_sec = extraction_result.extraction_time_sec
            report.quality_score = extraction_result.quality_score
            report.extracted_text_length = extraction_result.text_length

            print(f"[SUCCESS] Extraction complete:")
            print(f"   - Pages: {extraction_result.extracted_pages}/{extraction_result.total_pages}")
            print(f"   - Text: {extraction_result.text_length:,} chars")
            print(f"   - Quality: {extraction_result.quality_score:.1%}")
            print(f"   - Time: {extraction_result.extraction_time_sec:.2f}s")
            print(f"   - Files: {len(extraction_result.output_files)}")

        except Exception as e:
            report.status = "error"
            report.extraction_completed_at = datetime.now(timezone.utc)
            print(f"[ERROR] Extraction failed: {e}")
            session.commit()
            raise

        session.commit()
        return report

    def _create_source_report(
        self,
        metadata: PDFMetadata,
        session: Session,
    ) -> SourceReport:
        """Create new SourceReport record from metadata.

        Args:
            metadata: Extracted PDF metadata
            session: Database session

        Returns:
            New SourceReport object (not yet committed)
        """
        # Find or create city
        city = None
        if metadata.inferred_city:
            city = session.execute(
                select(City).where(City.name_en == metadata.inferred_city)
            ).scalar_one_or_none()

        # Find or create period
        period = None
        if metadata.inferred_period:
            # Parse period (format: YYYY-H1 or YYYY-H2)
            year_str, half_str = metadata.inferred_period.split("-")
            year = int(year_str)
            half = int(half_str[1])  # Extract 1 or 2 from H1/H2

            period = session.execute(
                select(ReportPeriod).where(
                    ReportPeriod.year == year,
                    ReportPeriod.half == half,
                )
            ).scalar_one_or_none()

            if not period:
                # Create new period
                period = ReportPeriod(year=year, half=half)
                session.add(period)
                session.flush()

        # Create report record
        report = SourceReport(
            filename=metadata.filename,
            report_type=metadata.inferred_report_type or "unknown",
            city_id=city.id if city else None,
            period_id=period.id if period else None,
            page_count=metadata.pdf_pages,
            pdf_path=metadata.file_path,
            file_size_mb=metadata.file_size_mb,
            pdf_created_at=metadata.pdf_created,
            status="pending",
        )

        session.add(report)
        session.flush()

        return report

    def batch_ingest(
        self,
        pdf_paths: list[str | Path],
        force: bool = False,
    ) -> dict:
        """Ingest multiple PDFs.

        Args:
            pdf_paths: List of PDF file paths
            force: If True, reprocess existing files

        Returns:
            Dict with success/failure counts
        """
        results = {
            "total": len(pdf_paths),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "reports": [],
        }

        with get_session() as session:
            for pdf_path in pdf_paths:
                try:
                    print(f"\n{'='*80}")
                    report = self.ingest_pdf(pdf_path, session, force=force)
                    results["success"] += 1
                    results["reports"].append(report.id)

                except ValueError as e:
                    # Already exists
                    print(f"[SKIP] Skipped: {Path(pdf_path).name} ({e})")
                    results["skipped"] += 1

                except Exception as e:
                    print(f"[FAIL] Failed: {Path(pdf_path).name} ({e})")
                    results["failed"] += 1

        return results

    def scan_and_ingest(self) -> dict:
        """Scan directory and ingest all new PDFs.

        Returns:
            Dict with ingestion results
        """
        print(f"[SCAN] Scanning directory: {self.watch_dir}")

        with get_session() as session:
            new_pdfs = self.scan_for_new_pdfs(session)

        print(f"[FOUND] {len(new_pdfs)} new PDF(s)")

        if not new_pdfs:
            return {"total": 0, "success": 0, "failed": 0, "skipped": 0}

        return self.batch_ingest(new_pdfs)

    def get_ingestion_status(self, session: Session) -> dict:
        """Get summary of ingestion status.

        Args:
            session: Database session

        Returns:
            Dict with status counts
        """
        from sqlalchemy import func

        # Count by status
        stmt = select(
            SourceReport.status,
            func.count(SourceReport.id).label("count")
        ).group_by(SourceReport.status)

        status_counts = {}
        for status, count in session.execute(stmt):
            status_counts[status or "unknown"] = count

        # Count total PDFs in watch directory
        total_pdfs = len(list(self.watch_dir.glob("*.pdf")))

        return {
            "total_pdfs_in_directory": total_pdfs,
            "total_in_database": sum(status_counts.values()),
            "status_breakdown": status_counts,
        }


def ingest_single_pdf(
    pdf_path: str | Path,
    watch_dir: Optional[str | Path] = None,
    force: bool = False,
) -> dict:
    """Convenience function to ingest a single PDF.

    Args:
        pdf_path: Path to PDF file
        watch_dir: Directory containing PDFs (defaults to pdf_path's parent)
        force: If True, reprocess even if already exists

    Returns:
        Dict with report details
    """
    pdf_path = Path(pdf_path)

    if watch_dir is None:
        watch_dir = pdf_path.parent

    orchestrator = IngestionOrchestrator(watch_dir)

    with get_session() as session:
        report = orchestrator.ingest_pdf(pdf_path, session, force=force)

        # Return report data as dict (detached from session)
        return {
            "id": report.id,
            "filename": report.filename,
            "report_type": report.report_type,
            "page_count": report.page_count,
            "file_size_mb": report.file_size_mb,
            "status": report.status,
            "quality_score": report.quality_score,
            "extraction_time_sec": report.extraction_time_sec,
            "extracted_text_length": report.extracted_text_length,
        }
