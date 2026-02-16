"""CLI command: Scan folder and ingest new PDFs."""

import argparse
import sys
from pathlib import Path

from src.collectors.orchestrator import IngestionOrchestrator
from src.collectors.cli_utils import (
    print_header, print_success, print_error, print_warning, print_info,
    print_section, print_summary_box, format_size, format_duration, ProgressBar
)


def main():
    """Scan folder and ingest new PDFs."""
    parser = argparse.ArgumentParser(
        description="Scan directory for new PDFs and ingest them",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan default directory
  python -m src.collectors.cli_scan_folder

  # Scan specific directory
  python -m src.collectors.cli_scan_folder /path/to/pdfs

  # Dry run (show what would be ingested)
  python -m src.collectors.cli_scan_folder --dry-run

  # Force reprocess existing files
  python -m src.collectors.cli_scan_folder --force

  # Verbose output
  python -m src.collectors.cli_scan_folder -v
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='user_resources/D_colect',
        help='Directory to scan for PDFs (default: user_resources/D_colect)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be ingested without actually ingesting'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocess files that are already ingested'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--output-dir',
        help='Directory to save extracted text (default: <directory>/extracted)'
    )

    args = parser.parse_args()

    # Validate directory
    watch_dir = Path(args.directory)
    if not watch_dir.exists():
        print_error(f"Directory does not exist: {args.directory}")
        sys.exit(1)

    if not watch_dir.is_dir():
        print_error(f"Not a directory: {args.directory}")
        sys.exit(1)

    # Print header
    print_header("PDF FOLDER SCAN & INGEST")

    print_info(f"Directory: {watch_dir.absolute()}")
    if args.dry_run:
        print_warning("DRY RUN MODE - No files will be ingested")
    if args.force:
        print_warning("FORCE MODE - Will reprocess existing files")
    print()

    # Initialize orchestrator
    orchestrator = IngestionOrchestrator(
        watch_dir=watch_dir,
        extracted_text_dir=args.output_dir
    )

    # Scan for new PDFs
    print_section("Scanning for PDFs")

    from src.db.connection import get_session
    with get_session() as session:
        new_pdfs = orchestrator.scan_for_new_pdfs(session)

    if not new_pdfs:
        print_success("No new PDFs found. All files are already ingested.")
        return

    print_info(f"Found {len(new_pdfs)} new PDF(s):")
    for pdf in new_pdfs:
        print(f"  • {pdf.name}")

    if args.dry_run:
        print()
        print_warning("Dry run complete. No files were ingested.")
        return

    # Confirm ingestion
    print()
    response = input(f"Ingest {len(new_pdfs)} PDF(s)? [Y/n]: ").strip().lower()
    if response and response not in ['y', 'yes']:
        print_info("Aborted by user")
        return

    # Ingest PDFs
    print_section("Ingesting PDFs")

    progress = ProgressBar(len(new_pdfs))
    results = {
        "success": [],
        "failed": [],
        "skipped": []
    }

    for i, pdf_path in enumerate(new_pdfs):
        progress.update(i, f"Processing {pdf_path.name}")

        try:
            with get_session() as session:
                report = orchestrator.ingest_pdf(pdf_path, session, force=args.force)

                results["success"].append({
                    "name": report.filename,
                    "id": report.id,
                    "pages": report.page_count,
                    "size_mb": report.file_size_mb,
                    "quality": report.quality_score,
                    "time": report.extraction_time_sec,
                })

        except ValueError as e:
            # Already exists
            results["skipped"].append(pdf_path.name)
            if args.verbose:
                print()
                print_warning(f"Skipped: {pdf_path.name} ({e})")

        except Exception as e:
            results["failed"].append({"name": pdf_path.name, "error": str(e)})
            if args.verbose:
                print()
                print_error(f"Failed: {pdf_path.name} - {e}")

    progress.finish("Complete")

    # Print summary
    print_section("Summary")

    summary_items = {
        "Total PDFs": str(len(new_pdfs)),
        "Successfully Ingested": f"{len(results['success'])} (green)",
        "Skipped": f"{len(results['skipped'])} (yellow)",
        "Failed": f"{len(results['failed'])} (red)"
    }

    if results["success"]:
        total_pages = sum(r["pages"] for r in results["success"])
        total_size = sum(r["size_mb"] for r in results["success"])
        total_time = sum(r["time"] for r in results["success"])
        avg_quality = sum(r["quality"] for r in results["success"]) / len(results["success"])

        summary_items["Total Pages"] = f"{total_pages:,}"
        summary_items["Total Size"] = format_size(total_size)
        summary_items["Total Time"] = format_duration(total_time)
        summary_items["Avg Quality"] = f"{avg_quality:.1%}"

    print_summary_box("Ingestion Results", summary_items)

    # Print details if verbose
    if args.verbose and results["success"]:
        print_section("Ingested Files")
        for r in results["success"]:
            print(f"  [{r['id']:3d}] {r['name']}")
            print(f"        Pages: {r['pages']}, Size: {format_size(r['size_mb'])}, "
                  f"Quality: {r['quality']:.1%}, Time: {format_duration(r['time'])}")

    if results["failed"]:
        print_section("Failed Files")
        for item in results["failed"]:
            print_error(f"  {item['name']}: {item['error']}")

    # Exit code
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
