"""Simple script to start PDF file watcher."""

import sys
from pathlib import Path

from src.collectors.watcher import watch_directory


def main():
    """Start PDF watcher with command line arguments."""
    # Parse arguments
    watch_dir = sys.argv[1] if len(sys.argv) > 1 else "user_resources/D_colect"
    scan_on_start = "--no-scan" not in sys.argv
    debounce_seconds = 2.0

    # Check for debounce argument
    for arg in sys.argv:
        if arg.startswith("--debounce="):
            try:
                debounce_seconds = float(arg.split("=")[1])
            except ValueError:
                print(f"Invalid debounce value: {arg}")
                sys.exit(1)

    # Validate watch directory
    watch_path = Path(watch_dir)
    if not watch_path.exists():
        print(f"Error: Directory does not exist: {watch_dir}")
        sys.exit(1)

    print("="*80)
    print("PDF FILE WATCHER")
    print("="*80)
    print(f"Watch directory: {watch_dir}")
    print(f"Scan on start: {scan_on_start}")
    print(f"Debounce: {debounce_seconds}s")
    print()
    print("Press Ctrl+C to stop")
    print("="*80)
    print()

    # Start watcher
    try:
        watch_directory(
            watch_dir=watch_dir,
            scan_on_start=scan_on_start,
            debounce_seconds=debounce_seconds,
        )
    except KeyboardInterrupt:
        print("\nWatcher stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
