"""CLI command: Ingest a single PDF file."""

import argparse
import sys
from pathlib import Path

from src.collectors.orchestrator import ingest_single_pdf
from src.collectors.cli_utils import (
    print_header, print_success, print_error, print_info,
    print_section, print_summary_box, format_size, format_duration
)


def main():
    """Ingest a single PDF file."""
    parser = argparse.ArgumentParser(
        description="Ingest a single PDF file into the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a PDF
  python -m src.collectors.cli_ingest_pdf report.pdf

  # Force reprocess existing file
  python -m src.collectors.cli_ingest_pdf report.pdf --force

  # Specify custom output directory
  python -m src.collectors.cli_ingest_pdf report.pdf --output-dir /path/to/extracted

  # Verbose output
  python -m src.collectors.cli_ingest_pdf report.pdf -v
        """
    )

    parser.add_argument(
        'pdf_file',
        help='Path to PDF file to ingest'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocess if file is already ingested'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--output-dir',
        help='Directory to save extracted text (default: <pdf_directory>/extracted)'
    )

    args = parser.parse_args()

    # Validate file
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print_error(f"File does not exist: {args.pdf_file}")
        sys.exit(1)

    if not pdf_path.is_file():
        print_error(f"Not a file: {args.pdf_file}")
        sys.exit(1)

    if pdf_path.suffix.lower() != '.pdf':
        print_error(f"Not a PDF file: {args.pdf_file}")
        sys.exit(1)

    # Print header
    print_header("PDF INGESTION")

    print_info(f"File: {pdf_path.name}")
    print_info(f"Path: {pdf_path.absolute()}")
    if args.force:
        print_info("Mode: FORCE (will reprocess if already ingested)")
    print()

    # Extract metadata first
    print_section("Extracting Metadata")

    from src.collectors.pdf_metadata import extract_pdf_metadata

    try:
        metadata = extract_pdf_metadata(pdf_path)
    except Exception as e:
        print_error(f"Failed to extract metadata: {e}")
        sys.exit(1)

    print(f"  Filename: {metadata.filename}")
    print(f"  Size: {format_size(metadata.file_size_mb)}")
    print(f"  Pages: {metadata.pdf_pages}")
    print(f"  Report Type: {metadata.inferred_report_type or 'Unknown'}")
    print(f"  City: {metadata.inferred_city or 'N/A'}")
    print(f"  Period: {metadata.inferred_period or 'N/A'}")

    if metadata.pdf_title:
        print(f"  PDF Title: {metadata.pdf_title}")
    if metadata.pdf_author:
        print(f"  Author: {metadata.pdf_author}")

    # Confirm ingestion
    print()
    if not args.force:
        response = input("Proceed with ingestion? [Y/n]: ").strip().lower()
        if response and response not in ['y', 'yes']:
            print_info("Aborted by user")
            return

    # Ingest file
    print_section("Ingesting PDF")

    try:
        # Determine watch_dir
        watch_dir = pdf_path.parent if not args.output_dir else Path(args.output_dir).parent

        result = ingest_single_pdf(
            pdf_path=pdf_path,
            watch_dir=watch_dir,
            force=args.force
        )

        print_success(f"Ingested successfully!")
        print()

        # Print summary
        summary_items = {
            "Report ID": str(result["id"]),
            "Filename": result["filename"],
            "Report Type": result["report_type"],
            "Pages": str(result["page_count"]),
            "Size": format_size(result["file_size_mb"]),
            "Status": result["status"],
            "Extraction Time": format_duration(result["extraction_time_sec"]),
            "Quality Score": f"{result['quality_score']:.1%}",
            "Text Length": f"{result['extracted_text_length']:,} chars"
        }

        print_summary_box("Ingestion Results", summary_items)

    except ValueError as e:
        print_error(f"File already ingested: {e}")
        print_info("Use --force to reprocess")
        sys.exit(1)

    except Exception as e:
        print_error(f"Ingestion failed: {e}")
        if args.verbose:
            import traceback
            print()
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
