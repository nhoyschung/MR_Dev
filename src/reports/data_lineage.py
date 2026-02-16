"""Data lineage tracking and quality monitoring system."""

from datetime import date, datetime, timezone
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session

from src.db.models import DataLineage, SourceReport, City, ReportPeriod
from src.reports.charts import _fig_to_base64
from src.reports.renderer import render_template


def get_record_lineage(
    session: Session, table_name: str, record_id: int
) -> Optional[dict]:
    """Get lineage information for a specific record.

    Args:
        session: Database session
        table_name: Table name (e.g., 'projects', 'price_records')
        record_id: Record ID

    Returns:
        Dict with lineage info or None if not found
    """
    stmt = (
        select(DataLineage, SourceReport)
        .join(SourceReport, DataLineage.source_report_id == SourceReport.id)
        .where(
            DataLineage.table_name == table_name,
            DataLineage.record_id == record_id
        )
    )
    result = session.execute(stmt).first()

    if not result:
        return None

    lineage, report = result
    return {
        "table_name": lineage.table_name,
        "record_id": lineage.record_id,
        "source_report": report.filename,
        "report_type": report.report_type,
        "page_number": lineage.page_number,
        "confidence_score": lineage.confidence_score,
        "extracted_at": lineage.extracted_at,
    }


def get_source_impact(session: Session, source_report_id: int) -> dict:
    """Analyze impact of a source report (how many records it created).

    Args:
        session: Database session
        source_report_id: Source report ID

    Returns:
        Dict with impact statistics
    """
    report = session.execute(
        select(SourceReport).where(SourceReport.id == source_report_id)
    ).scalar_one_or_none()

    if not report:
        return {}

    # Count records by table
    stmt = (
        select(
            DataLineage.table_name,
            func.count(DataLineage.id)
        )
        .where(DataLineage.source_report_id == source_report_id)
        .group_by(DataLineage.table_name)
        .order_by(func.count(DataLineage.id).desc())
    )
    table_counts = session.execute(stmt).all()

    total_records = sum(count for _, count in table_counts)

    return {
        "source_report": report.filename,
        "report_type": report.report_type,
        "total_records": total_records,
        "table_breakdown": [
            {"table": table, "count": count}
            for table, count in table_counts
        ],
    }


def get_quality_metrics(session: Session) -> dict:
    """Get overall data quality metrics based on confidence scores.

    Args:
        session: Database session

    Returns:
        Dict with quality statistics
    """
    # Overall confidence distribution
    stmt = (
        select(
            func.count(DataLineage.id),
            func.avg(DataLineage.confidence_score),
            func.min(DataLineage.confidence_score),
            func.max(DataLineage.confidence_score),
        )
        .where(DataLineage.confidence_score.isnot(None))
    )
    total, avg_conf, min_conf, max_conf = session.execute(stmt).one()

    # Count by confidence ranges
    high_conf = session.execute(
        select(func.count(DataLineage.id))
        .where(DataLineage.confidence_score >= 0.8)
    ).scalar() or 0

    medium_conf = session.execute(
        select(func.count(DataLineage.id))
        .where(
            DataLineage.confidence_score >= 0.5,
            DataLineage.confidence_score < 0.8
        )
    ).scalar() or 0

    low_conf = session.execute(
        select(func.count(DataLineage.id))
        .where(DataLineage.confidence_score < 0.5)
    ).scalar() or 0

    return {
        "total_records": total or 0,
        "avg_confidence": avg_conf or 0,
        "min_confidence": min_conf or 0,
        "max_confidence": max_conf or 0,
        "high_confidence": high_conf,
        "medium_confidence": medium_conf,
        "low_confidence": low_conf,
    }


def get_extraction_timeline(session: Session) -> list[dict]:
    """Get timeline of data extraction activities.

    Args:
        session: Database session

    Returns:
        List of extraction events by date
    """
    # Group by date
    stmt = (
        select(
            func.date(DataLineage.extracted_at).label('date'),
            func.count(DataLineage.id).label('count')
        )
        .where(DataLineage.extracted_at.isnot(None))
        .group_by(func.date(DataLineage.extracted_at))
        .order_by(func.date(DataLineage.extracted_at))
    )
    results = session.execute(stmt).all()

    return [
        {"date": str(date_val), "count": count}
        for date_val, count in results
    ]


def get_table_coverage(session: Session) -> list[dict]:
    """Get coverage statistics for each table.

    Args:
        session: Database session

    Returns:
        List of tables with lineage coverage
    """
    stmt = (
        select(
            DataLineage.table_name,
            func.count(DataLineage.id),
            func.count(distinct(DataLineage.source_report_id))
        )
        .group_by(DataLineage.table_name)
        .order_by(func.count(DataLineage.id).desc())
    )
    results = session.execute(stmt).all()

    return [
        {
            "table_name": table,
            "record_count": count,
            "source_count": sources,
        }
        for table, count, sources in results
    ]


def _lineage_distribution_chart(table_coverage: list[dict]) -> Optional[str]:
    """Create a bar chart showing lineage distribution across tables.

    Args:
        table_coverage: List of table coverage dicts

    Returns:
        Base64-encoded PNG image data URL
    """
    if not table_coverage:
        return None

    fig, ax = plt.subplots(figsize=(12, max(6, len(table_coverage) * 0.4)))

    tables = [item["table_name"] for item in table_coverage]
    counts = [item["record_count"] for item in table_coverage]

    bars = ax.barh(tables, counts, color='steelblue', edgecolor='darkblue', linewidth=1.2)

    # Add value labels
    for bar, count in zip(bars, counts):
        ax.text(count + max(counts) * 0.02, bar.get_y() + bar.get_height()/2.,
                f'{count:,}',
                ha='left', va='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('Number of Records', fontsize=11, fontweight='bold')
    ax.set_title('Data Lineage Coverage by Table', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    return _fig_to_base64(fig)


def _quality_distribution_chart(quality_metrics: dict) -> Optional[str]:
    """Create a pie chart showing data quality distribution.

    Args:
        quality_metrics: Quality metrics dict

    Returns:
        Base64-encoded PNG image data URL
    """
    high = quality_metrics.get("high_confidence", 0)
    medium = quality_metrics.get("medium_confidence", 0)
    low = quality_metrics.get("low_confidence", 0)

    if high + medium + low == 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 8))

    sizes = [high, medium, low]
    labels = [
        f'High (≥80%)\n{high:,} records',
        f'Medium (50-80%)\n{medium:,} records',
        f'Low (<50%)\n{low:,} records'
    ]
    colors = ['green', 'orange', 'red']
    explode = (0.05, 0, 0)

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, explode=explode,
        autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'}
    )

    ax.set_title('Data Quality Distribution by Confidence Score',
                 fontsize=13, fontweight='bold', pad=20)

    plt.tight_layout()
    return _fig_to_base64(fig)


def _extraction_timeline_chart(timeline: list[dict]) -> Optional[str]:
    """Create a line chart showing extraction timeline.

    Args:
        timeline: List of timeline dicts

    Returns:
        Base64-encoded PNG image data URL
    """
    if not timeline:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    dates = [item["date"] for item in timeline]
    counts = [item["count"] for item in timeline]

    ax.plot(dates, counts, marker='o', linewidth=2, markersize=8,
            color='steelblue', markerfacecolor='coral', markeredgecolor='black')

    # Add value labels
    for date_val, count in zip(dates, counts):
        ax.text(date_val, count, f'{count:,}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('Records Extracted', fontsize=11, fontweight='bold')
    ax.set_title('Data Extraction Timeline', fontsize=13, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    return _fig_to_base64(fig)


def _source_impact_chart(source_reports: list[dict]) -> Optional[str]:
    """Create a horizontal bar chart showing impact of source reports.

    Args:
        source_reports: List of source report impact dicts

    Returns:
        Base64-encoded PNG image data URL
    """
    if not source_reports:
        return None

    fig, ax = plt.subplots(figsize=(12, max(6, len(source_reports) * 0.4)))

    names = [r["filename"][:40] for r in source_reports]
    counts = [r["total_records"] for r in source_reports]

    bars = ax.barh(names, counts, color='coral', edgecolor='darkred', linewidth=1.2)

    # Add value labels
    for bar, count in zip(bars, counts):
        ax.text(count + max(counts) * 0.02, bar.get_y() + bar.get_height()/2.,
                f'{count:,}',
                ha='left', va='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('Records Generated', fontsize=11, fontweight='bold')
    ax.set_title('Source Report Impact Analysis', fontsize=13, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()
    return _fig_to_base64(fig)


def render_lineage_report(session: Session) -> str:
    """Generate a comprehensive data lineage tracking report.

    Args:
        session: Database session

    Returns:
        Rendered markdown report string
    """
    # Get all source reports
    all_reports = session.execute(
        select(SourceReport).order_by(SourceReport.ingested_at.desc())
    ).scalars().all()

    source_impacts = []
    for report in all_reports:
        impact = get_source_impact(session, report.id)
        if impact and impact.get("total_records", 0) > 0:
            source_impacts.append({
                "filename": report.filename,
                "report_type": report.report_type,
                "total_records": impact["total_records"],
                "table_breakdown": impact.get("table_breakdown", []),
                "ingested_at": report.ingested_at,
                "status": report.status,
            })

    # Get quality metrics
    quality = get_quality_metrics(session)

    # Get extraction timeline
    timeline = get_extraction_timeline(session)

    # Get table coverage
    coverage = get_table_coverage(session)

    # Calculate summary stats
    total_sources = len(all_reports)
    active_sources = sum(1 for r in all_reports if r.status == "ingested")
    total_lineage_records = session.execute(
        select(func.count(DataLineage.id))
    ).scalar() or 0

    # Generate charts
    chart_distribution = _lineage_distribution_chart(coverage)
    chart_quality = _quality_distribution_chart(quality)
    chart_timeline = _extraction_timeline_chart(timeline)
    chart_impact = _source_impact_chart(source_impacts[:15])  # Top 15

    context = {
        "generated_date": date.today().isoformat(),
        "total_sources": total_sources,
        "active_sources": active_sources,
        "total_lineage_records": total_lineage_records,
        "quality_metrics": quality,
        "table_coverage": coverage,
        "source_impacts": source_impacts,
        "timeline": timeline,
        "chart_distribution": chart_distribution,
        "chart_quality": chart_quality,
        "chart_timeline": chart_timeline,
        "chart_impact": chart_impact,
    }

    return render_template("data_lineage.md.j2", **context)
