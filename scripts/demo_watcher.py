"""Demo script to show watcher functionality without blocking."""

import time
from pathlib import Path
from src.collectors.watcher import PDFWatcher


def main():
    """Demo watcher functionality."""
    print("="*80)
    print("PDF WATCHER DEMO")
    print("="*80)
    print()

    # Initialize watcher
    watch_dir = "user_resources/D_colect"
    watcher = PDFWatcher(watch_dir)

    print(f"1. Watcher initialized")
    print(f"   Watch directory: {watch_dir}")
    print(f"   Extract directory: {watcher.orchestrator.extracted_text_dir}")
    print()

    # Check initial status
    status = watcher.get_status()
    print(f"2. Initial status:")
    print(f"   Running: {status['running']}")
    print(f"   Watch dir: {status['watch_dir']}")
    print()

    # Check for new PDFs
    from src.db.connection import get_session
    with get_session() as session:
        new_pdfs = watcher.orchestrator.scan_for_new_pdfs(session)
        print(f"3. New PDFs in directory: {len(new_pdfs)}")
        if new_pdfs:
            for pdf in new_pdfs[:3]:  # Show first 3
                print(f"   - {pdf.name}")
            if len(new_pdfs) > 3:
                print(f"   ... and {len(new_pdfs) - 3} more")
        else:
            print(f"   (All PDFs already ingested)")
        print()

    # Get ingestion status
    with get_session() as session:
        ingest_status = watcher.orchestrator.get_ingestion_status(session)
        print(f"4. Ingestion status:")
        print(f"   PDFs in directory: {ingest_status['total_pdfs_in_directory']}")
        print(f"   Records in database: {ingest_status['total_in_database']}")
        print(f"   Status breakdown:")
        for status_name, count in ingest_status['status_breakdown'].items():
            print(f"     - {status_name}: {count}")
        print()

    # Start and stop immediately (just to show it works)
    print(f"5. Testing start/stop:")
    watcher.start()
    print(f"   Started: {watcher._running}")

    # Wait a moment
    time.sleep(0.5)

    # Check status while running
    status = watcher.get_status()
    print(f"   Runtime: {status.get('runtime_seconds', 0):.2f}s")

    # Stop
    watcher.stop()
    print(f"   Stopped: {not watcher._running}")
    print()

    print("="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print()
    print("To run watcher continuously:")
    print("  python scripts/watch_pdfs.py")
    print()
    print("Or in Python code:")
    print("  from src.collectors.watcher import watch_directory")
    print("  watch_directory('user_resources/D_colect')")
    print()


if __name__ == "__main__":
    main()
