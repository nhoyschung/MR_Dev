"""CLI command: Show ingestion status and statistics."""

import argparse
from pathlib import Path

from sqlalchemy import select, func

from src.db.connection import get_session
from src.db.models import SourceReport, City, ReportPeriod
from src.collectors.cli_utils import (
    print_header, print_section, print_table, print_summary_box,
    format_size, format_duration, format_timestamp
)


def main():
    """Show ingestion status and statistics."""
    parser = argparse.ArgumentParser(
        description="Show PDF ingestion status and statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show basic status
  python -m src.collectors.cli_status

  # Show detailed report list
  python -m src.collectors.cli_status --detailed

  # Show statistics
  python -m src.collectors.cli_status --stats

  # Show everything
  python -m src.collectors.cli_status --all
        """
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed list of all ingested PDFs'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show detailed statistics'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all information (detailed + stats)'
    )

    parser.add_argument(
        '--watch-dir',
        default='user_resources/D_colect',
        help='Watch directory to check (default: user_resources/D_colect)'
    )

    args = parser.parse_args()

    if args.all:
        args.detailed = True
        args.stats = True

    # Print header
    print_header("PDF INGESTION STATUS")

    with get_session() as session:
        # Get overall counts
        total_reports = session.execute(
            select(func.count(SourceReport.id))
        ).scalar()

        pdf_reports = session.execute(
            select(func.count(SourceReport.id)).where(
                SourceReport.pdf_path.isnot(None)
            )
        ).scalar()

        # Count PDFs in directory
        watch_dir = Path(args.watch_dir)
        pdfs_in_dir = len(list(watch_dir.glob("*.pdf"))) if watch_dir.exists() else 0

        # Status breakdown
        status_stmt = select(
            SourceReport.status,
            func.count(SourceReport.id).label('count')
        ).group_by(SourceReport.status)

        status_counts = {status: count for status, count in session.execute(status_stmt)}

        # Print summary
        summary_items = {
            "Total Reports in DB": str(total_reports),
            "PDF Files Tracked": str(pdf_reports),
            "PDFs in Directory": f"{pdfs_in_dir} ({watch_dir})",
            "Unprocessed": str(max(0, pdfs_in_dir - pdf_reports)),
        }

        # Add status breakdown
        for status, count in sorted(status_counts.items()):
            summary_items[f"Status: {status}"] = str(count)

        print_summary_box("Overview", summary_items)

        # Detailed report list
        if args.detailed:
            print_section("Ingested PDFs (with PDF tracking)")

            stmt = select(SourceReport).where(
                SourceReport.pdf_path.isnot(None)
            ).order_by(SourceReport.id.desc()).limit(50)

            reports = session.execute(stmt).scalars().all()

            if reports:
                headers = ["ID", "Filename", "Type", "Pages", "Size", "Quality", "Status"]
                rows = []

                for r in reports:
                    rows.append([
                        str(r.id),
                        r.filename[:40] + "..." if len(r.filename) > 40 else r.filename,
                        r.report_type[:15],
                        str(r.page_count or 0),
                        format_size(r.file_size_mb or 0),
                        f"{r.quality_score:.1%}" if r.quality_score else "N/A",
                        r.status or "N/A"
                    ])

                print_table(headers, rows)

                if len(reports) == 50:
                    print("\n(Showing latest 50 reports)")
            else:
                print("(No PDF reports found)")

        # Statistics
        if args.stats:
            print_section("Statistics")

            # Size statistics
            size_stats = session.execute(
                select(
                    func.sum(SourceReport.file_size_mb).label('total_size'),
                    func.avg(SourceReport.file_size_mb).label('avg_size'),
                    func.max(SourceReport.file_size_mb).label('max_size'),
                ).where(SourceReport.pdf_path.isnot(None))
            ).first()

            # Page statistics
            page_stats = session.execute(
                select(
                    func.sum(SourceReport.page_count).label('total_pages'),
                    func.avg(SourceReport.page_count).label('avg_pages'),
                    func.max(SourceReport.page_count).label('max_pages'),
                ).where(SourceReport.pdf_path.isnot(None))
            ).first()

            # Quality statistics
            quality_stats = session.execute(
                select(
                    func.avg(SourceReport.quality_score).label('avg_quality'),
                    func.min(SourceReport.quality_score).label('min_quality'),
                    func.max(SourceReport.quality_score).label('max_quality'),
                ).where(
                    SourceReport.pdf_path.isnot(None),
                    SourceReport.quality_score.isnot(None)
                )
            ).first()

            # Time statistics
            time_stats = session.execute(
                select(
                    func.sum(SourceReport.extraction_time_sec).label('total_time'),
                    func.avg(SourceReport.extraction_time_sec).label('avg_time'),
                ).where(
                    SourceReport.pdf_path.isnot(None),
                    SourceReport.extraction_time_sec.isnot(None)
                )
            ).first()

            # Text statistics
            text_stats = session.execute(
                select(
                    func.sum(SourceReport.extracted_text_length).label('total_chars'),
                    func.avg(SourceReport.extracted_text_length).label('avg_chars'),
                ).where(
                    SourceReport.pdf_path.isnot(None),
                    SourceReport.extracted_text_length.isnot(None)
                )
            ).first()

            stats_items = {}

            if size_stats and size_stats.total_size:
                stats_items["Total Size"] = format_size(size_stats.total_size)
                stats_items["Avg Size"] = format_size(size_stats.avg_size)
                stats_items["Max Size"] = format_size(size_stats.max_size)

            if page_stats and page_stats.total_pages:
                stats_items["Total Pages"] = f"{int(page_stats.total_pages):,}"
                stats_items["Avg Pages"] = f"{page_stats.avg_pages:.0f}"
                stats_items["Max Pages"] = str(int(page_stats.max_pages))

            if quality_stats and quality_stats.avg_quality:
                stats_items["Avg Quality"] = f"{quality_stats.avg_quality:.1%}"
                stats_items["Quality Range"] = f"{quality_stats.min_quality:.1%} - {quality_stats.max_quality:.1%}"

            if time_stats and time_stats.total_time:
                stats_items["Total Extraction Time"] = format_duration(time_stats.total_time)
                stats_items["Avg Extraction Time"] = format_duration(time_stats.avg_time)

            if text_stats and text_stats.total_chars:
                stats_items["Total Text Extracted"] = f"{int(text_stats.total_chars):,} chars"
                stats_items["Avg Text per PDF"] = f"{int(text_stats.avg_chars):,} chars"

            if stats_items:
                print_summary_box("PDF Statistics", stats_items)
            else:
                print("(No statistics available)")

            # Breakdown by report type
            print_section("Breakdown by Report Type")

            type_stmt = select(
                SourceReport.report_type,
                func.count(SourceReport.id).label('count'),
                func.sum(SourceReport.page_count).label('total_pages'),
                func.sum(SourceReport.file_size_mb).label('total_size'),
            ).where(
                SourceReport.pdf_path.isnot(None)
            ).group_by(SourceReport.report_type)

            type_data = session.execute(type_stmt).all()

            if type_data:
                headers = ["Report Type", "Count", "Total Pages", "Total Size"]
                rows = []

                for report_type, count, pages, size in type_data:
                    rows.append([
                        report_type or "unknown",
                        str(count),
                        str(int(pages or 0)),
                        format_size(size or 0)
                    ])

                print_table(headers, rows)
            else:
                print("(No data)")

            # Breakdown by city
            print_section("Breakdown by City")

            city_stmt = select(
                City.name_en,
                func.count(SourceReport.id).label('count'),
            ).join(
                SourceReport, SourceReport.city_id == City.id
            ).where(
                SourceReport.pdf_path.isnot(None)
            ).group_by(City.name_en)

            city_data = session.execute(city_stmt).all()

            if city_data:
                headers = ["City", "Count"]
                rows = [[city, str(count)] for city, count in city_data]
                print_table(headers, rows)
            else:
                print("(No city data)")

            # Recent ingestions
            print_section("Recent Ingestions (Last 10)")

            recent_stmt = select(SourceReport).where(
                SourceReport.pdf_path.isnot(None),
                SourceReport.extraction_completed_at.isnot(None)
            ).order_by(SourceReport.extraction_completed_at.desc()).limit(10)

            recent_reports = session.execute(recent_stmt).scalars().all()

            if recent_reports:
                headers = ["Time", "Filename", "Pages", "Quality"]
                rows = []

                for r in recent_reports:
                    rows.append([
                        format_timestamp(r.extraction_completed_at),
                        r.filename[:45] + "..." if len(r.filename) > 45 else r.filename,
                        str(r.page_count or 0),
                        f"{r.quality_score:.1%}" if r.quality_score else "N/A"
                    ])

                print_table(headers, rows)
            else:
                print("(No recent ingestions)")


if __name__ == "__main__":
    main()
