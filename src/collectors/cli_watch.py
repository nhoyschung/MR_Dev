"""CLI command: Start file watcher daemon."""

import argparse
import sys
from pathlib import Path

from src.collectors.watcher import PDFWatcher
from src.collectors.cli_utils import print_header, print_error, print_info


def main():
    """Start PDF file watcher daemon."""
    parser = argparse.ArgumentParser(
        description="Start file system watcher for automatic PDF ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Watch default directory
  python -m src.collectors.cli_watch

  # Watch specific directory
  python -m src.collectors.cli_watch /path/to/pdfs

  # Without initial scan
  python -m src.collectors.cli_watch --no-scan

  # Custom debounce time (for large files)
  python -m src.collectors.cli_watch --debounce 5.0

  # Custom output directory
  python -m src.collectors.cli_watch --output-dir /path/to/extracted
        """
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='user_resources/D_colect',
        help='Directory to watch for PDFs (default: user_resources/D_colect)'
    )

    parser.add_argument(
        '--no-scan',
        action='store_true',
        help='Skip initial scan for existing PDFs'
    )

    parser.add_argument(
        '--debounce',
        type=float,
        default=2.0,
        help='Debounce time in seconds (default: 2.0)'
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
    print_header("PDF FILE WATCHER")

    print_info(f"Watch Directory: {watch_dir.absolute()}")
    print_info(f"Debounce: {args.debounce}s")
    print_info(f"Initial Scan: {'No' if args.no_scan else 'Yes'}")

    if args.output_dir:
        print_info(f"Output Directory: {args.output_dir}")

    print()
    print_info("Press Ctrl+C to stop")
    print()

    # Initialize watcher
    try:
        watcher = PDFWatcher(
            watch_dir=watch_dir,
            extracted_text_dir=args.output_dir,
            debounce_seconds=args.debounce,
        )

        # Run watcher
        watcher.run(
            scan_on_start=not args.no_scan,
            run_forever=True
        )

    except KeyboardInterrupt:
        print()
        print_info("Watcher stopped by user")

    except Exception as e:
        print()
        print_error(f"Watcher error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
