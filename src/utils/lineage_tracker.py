"""Utility functions for data lineage tracking and management."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import DataLineage, SourceReport


def track_lineage(
    session: Session,
    table_name: str,
    record_id: int,
    source_report_id: int,
    page_number: Optional[int] = None,
    confidence_score: Optional[float] = None,
) -> DataLineage:
    """Create a data lineage record for a newly extracted record.

    Args:
        session: Database session
        table_name: Table name (e.g., 'projects', 'price_records')
        record_id: Record ID
        source_report_id: Source report ID
        page_number: Page number in source document
        confidence_score: Confidence score (0.0-1.0)

    Returns:
        Created DataLineage object
    """
    lineage = DataLineage(
        table_name=table_name,
        record_id=record_id,
        source_report_id=source_report_id,
        page_number=page_number,
        confidence_score=confidence_score,
        extracted_at=datetime.now(timezone.utc),
    )
    session.add(lineage)
    return lineage


def update_confidence(
    session: Session,
    table_name: str,
    record_id: int,
    new_confidence: float,
) -> bool:
    """Update confidence score for a lineage record.

    Args:
        session: Database session
        table_name: Table name
        record_id: Record ID
        new_confidence: New confidence score (0.0-1.0)

    Returns:
        True if updated, False if not found
    """
    lineage = session.query(DataLineage).filter_by(
        table_name=table_name,
        record_id=record_id
    ).first()

    if lineage:
        lineage.confidence_score = new_confidence
        return True
    return False


def find_records_from_source(
    session: Session,
    source_report_id: int,
    table_name: Optional[str] = None,
) -> list[DataLineage]:
    """Find all records extracted from a specific source report.

    Args:
        session: Database session
        source_report_id: Source report ID
        table_name: Optional table filter

    Returns:
        List of DataLineage objects
    """
    query = session.query(DataLineage).filter_by(
        source_report_id=source_report_id
    )

    if table_name:
        query = query.filter_by(table_name=table_name)

    return query.all()


def find_low_confidence_records(
    session: Session,
    threshold: float = 0.5,
    table_name: Optional[str] = None,
) -> list[DataLineage]:
    """Find records with low confidence scores for review.

    Args:
        session: Database session
        threshold: Confidence threshold (default 0.5)
        table_name: Optional table filter

    Returns:
        List of low-confidence DataLineage objects
    """
    query = session.query(DataLineage).filter(
        DataLineage.confidence_score < threshold,
        DataLineage.confidence_score.isnot(None)
    )

    if table_name:
        query = query.filter_by(table_name=table_name)

    return query.order_by(DataLineage.confidence_score).all()


def register_source_report(
    session: Session,
    filename: str,
    report_type: str,
    city_id: Optional[int] = None,
    period_id: Optional[int] = None,
    page_count: Optional[int] = None,
) -> SourceReport:
    """Register a new source report in the system.

    Args:
        session: Database session
        filename: Source filename
        report_type: Report type (e.g., 'market_analysis', 'case_study')
        city_id: Optional city ID
        period_id: Optional period ID
        page_count: Optional page count

    Returns:
        Created SourceReport object
    """
    report = SourceReport(
        filename=filename,
        report_type=report_type,
        city_id=city_id,
        period_id=period_id,
        page_count=page_count,
        ingested_at=datetime.now(timezone.utc),
        status="pending",
    )
    session.add(report)
    session.flush()  # Get ID without committing
    return report


def mark_source_ingested(
    session: Session,
    source_report_id: int,
) -> bool:
    """Mark a source report as successfully ingested.

    Args:
        session: Database session
        source_report_id: Source report ID

    Returns:
        True if updated, False if not found
    """
    report = session.query(SourceReport).filter_by(id=source_report_id).first()

    if report:
        report.status = "ingested"
        return True
    return False


def get_orphaned_records(session: Session, table_name: str) -> list[int]:
    """Find record IDs in a table that lack lineage tracking.

    Args:
        session: Database session
        table_name: Table name to check

    Returns:
        List of record IDs without lineage
    """
    # This is a simplified version - would need table-specific queries
    # For demonstration purposes, returns empty list
    # In production, would query the actual table and compare with lineage
    return []


def get_lineage_statistics(session: Session) -> dict:
    """Get summary statistics for the lineage system.

    Args:
        session: Database session

    Returns:
        Dict with lineage statistics
    """
    from sqlalchemy import func

    total_lineage = session.query(func.count(DataLineage.id)).scalar() or 0
    total_sources = session.query(func.count(SourceReport.id)).scalar() or 0

    avg_confidence = session.query(
        func.avg(DataLineage.confidence_score)
    ).filter(
        DataLineage.confidence_score.isnot(None)
    ).scalar() or 0

    tables_tracked = session.query(
        func.count(func.distinct(DataLineage.table_name))
    ).scalar() or 0

    return {
        "total_lineage_records": total_lineage,
        "total_source_reports": total_sources,
        "average_confidence": avg_confidence,
        "tables_tracked": tables_tracked,
    }


def validate_lineage_integrity(session: Session) -> dict:
    """Validate integrity of lineage tracking system.

    Args:
        session: Database session

    Returns:
        Dict with validation results
    """
    issues = []

    # Check for lineage records with missing source reports
    orphaned_lineage = session.query(DataLineage).filter(
        ~DataLineage.source_report_id.in_(
            session.query(SourceReport.id)
        )
    ).count()

    if orphaned_lineage > 0:
        issues.append(f"{orphaned_lineage} lineage records reference non-existent source reports")

    # Check for source reports with no lineage records
    unused_sources = session.query(SourceReport).filter(
        ~SourceReport.id.in_(
            session.query(DataLineage.source_report_id)
        ),
        SourceReport.status == "ingested"
    ).count()

    if unused_sources > 0:
        issues.append(f"{unused_sources} ingested source reports have no lineage records")

    # Check for records with null confidence scores
    null_confidence = session.query(DataLineage).filter(
        DataLineage.confidence_score.is_(None)
    ).count()

    if null_confidence > 0:
        issues.append(f"{null_confidence} lineage records have null confidence scores")

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "checks_performed": 3,
    }
