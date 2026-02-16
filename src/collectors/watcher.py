"""File system watcher for automated PDF collection."""

import time
import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime, timezone

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from src.collectors.orchestrator import IngestionOrchestrator
from src.db.connection import get_session


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFWatcherEventHandler(FileSystemEventHandler):
    """Event handler for PDF file system events."""

    def __init__(
        self,
        orchestrator: IngestionOrchestrator,
        debounce_seconds: float = 2.0,
        on_ingest_callback: Optional[Callable] = None,
    ):
        """Initialize event handler.

        Args:
            orchestrator: IngestionOrchestrator instance
            debounce_seconds: Wait time after file modification before processing
            on_ingest_callback: Optional callback function after successful ingestion
        """
        super().__init__()
        self.orchestrator = orchestrator
        self.debounce_seconds = debounce_seconds
        self.on_ingest_callback = on_ingest_callback

        # Track last modification times to debounce events
        self._last_modified = {}

        # Track files being processed to avoid duplicates
        self._processing = set()

    def on_created(self, event):
        """Handle file creation event.

        Args:
            event: FileSystemEvent object
        """
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            file_path = Path(event.src_path)

            # Only process PDF files
            if file_path.suffix.lower() == '.pdf':
                logger.info(f"[DETECT] New PDF created: {file_path.name}")
                self._schedule_ingestion(file_path)

    def on_modified(self, event):
        """Handle file modification event.

        Args:
            event: FileSystemEvent object
        """
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            file_path = Path(event.src_path)

            # Only process PDF files
            if file_path.suffix.lower() == '.pdf':
                # Debounce: only process if enough time has passed since last modification
                now = time.time()
                last_mod = self._last_modified.get(str(file_path), 0)

                if now - last_mod > self.debounce_seconds:
                    logger.info(f"[DETECT] PDF modified: {file_path.name}")
                    self._schedule_ingestion(file_path)

                self._last_modified[str(file_path)] = now

    def _schedule_ingestion(self, file_path: Path):
        """Schedule file for ingestion after debounce period.

        Args:
            file_path: Path to PDF file
        """
        file_key = str(file_path)

        # Skip if already processing
        if file_key in self._processing:
            logger.debug(f"[SKIP] Already processing: {file_path.name}")
            return

        # Wait for file to be fully written
        time.sleep(self.debounce_seconds)

        # Verify file still exists and is readable
        if not file_path.exists():
            logger.warning(f"[SKIP] File no longer exists: {file_path.name}")
            return

        # Mark as processing
        self._processing.add(file_key)

        try:
            self._ingest_file(file_path)
        finally:
            # Remove from processing set
            self._processing.discard(file_key)

    def _ingest_file(self, file_path: Path):
        """Ingest a single PDF file.

        Args:
            file_path: Path to PDF file
        """
        logger.info(f"[INGEST] Starting ingestion: {file_path.name}")

        try:
            with get_session() as session:
                report = self.orchestrator.ingest_pdf(
                    file_path,
                    session,
                    force=False  # Don't reprocess existing files
                )

                logger.info(
                    f"[SUCCESS] Ingested: {report.filename} "
                    f"(ID: {report.id}, Pages: {report.page_count}, "
                    f"Quality: {report.quality_score:.1%})"
                )

                # Call callback if provided
                if self.on_ingest_callback:
                    self.on_ingest_callback(report)

        except ValueError as e:
            # File already exists
            logger.info(f"[SKIP] Already ingested: {file_path.name}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to ingest {file_path.name}: {e}", exc_info=True)


class PDFWatcher:
    """PDF file system watcher with automatic ingestion."""

    def __init__(
        self,
        watch_dir: str | Path,
        extracted_text_dir: Optional[str | Path] = None,
        debounce_seconds: float = 2.0,
        on_ingest_callback: Optional[Callable] = None,
    ):
        """Initialize PDF watcher.

        Args:
            watch_dir: Directory to watch for PDF files
            extracted_text_dir: Directory to save extracted text (defaults to watch_dir/extracted)
            debounce_seconds: Wait time after file modification before processing
            on_ingest_callback: Optional callback function after successful ingestion
        """
        self.watch_dir = Path(watch_dir)
        self.watch_dir.mkdir(parents=True, exist_ok=True)

        # Initialize orchestrator
        self.orchestrator = IngestionOrchestrator(
            watch_dir=watch_dir,
            extracted_text_dir=extracted_text_dir,
        )

        # Initialize event handler
        self.event_handler = PDFWatcherEventHandler(
            orchestrator=self.orchestrator,
            debounce_seconds=debounce_seconds,
            on_ingest_callback=on_ingest_callback,
        )

        # Initialize observer
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.watch_dir),
            recursive=False  # Don't watch subdirectories
        )

        self._running = False
        self._start_time = None

    def start(self):
        """Start watching directory."""
        if self._running:
            logger.warning("Watcher is already running")
            return

        logger.info(f"[START] Starting PDF watcher")
        logger.info(f"[WATCH] Monitoring directory: {self.watch_dir}")
        logger.info(f"[WATCH] Extracted text will be saved to: {self.orchestrator.extracted_text_dir}")

        self._start_time = datetime.now(timezone.utc)
        self.observer.start()
        self._running = True

        logger.info("[READY] Watcher is now active. Press Ctrl+C to stop.")

    def stop(self):
        """Stop watching directory."""
        if not self._running:
            logger.warning("Watcher is not running")
            return

        logger.info("[STOP] Stopping PDF watcher...")
        self.observer.stop()
        self.observer.join()
        self._running = False

        if self._start_time:
            duration = datetime.now(timezone.utc) - self._start_time
            logger.info(f"[STOP] Watcher stopped. Runtime: {duration}")

    def run(self, scan_on_start: bool = True, run_forever: bool = True):
        """Run watcher with optional initial scan.

        Args:
            scan_on_start: If True, scan directory for new PDFs before watching
            run_forever: If True, run until Ctrl+C. If False, return after starting.
        """
        # Optional: Scan for existing PDFs first
        if scan_on_start:
            logger.info("[SCAN] Scanning for existing PDFs before starting watch...")
            try:
                results = self.orchestrator.scan_and_ingest()
                logger.info(
                    f"[SCAN] Initial scan complete: "
                    f"{results['success']} ingested, "
                    f"{results['skipped']} skipped, "
                    f"{results['failed']} failed"
                )
            except Exception as e:
                logger.error(f"[ERROR] Initial scan failed: {e}", exc_info=True)

        # Start watching
        self.start()

        if run_forever:
            try:
                # Run until interrupted
                while self._running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("[INTERRUPT] Received interrupt signal")
                self.stop()

    def get_status(self) -> dict:
        """Get watcher status.

        Returns:
            Dict with status information
        """
        status = {
            "running": self._running,
            "watch_dir": str(self.watch_dir),
            "extracted_text_dir": str(self.orchestrator.extracted_text_dir),
            "start_time": self._start_time.isoformat() if self._start_time else None,
        }

        if self._running and self._start_time:
            duration = datetime.now(timezone.utc) - self._start_time
            status["runtime_seconds"] = duration.total_seconds()

        return status


def watch_directory(
    watch_dir: str | Path,
    scan_on_start: bool = True,
    debounce_seconds: float = 2.0,
) -> None:
    """Convenience function to watch a directory for PDF files.

    Args:
        watch_dir: Directory to watch
        scan_on_start: If True, scan for existing PDFs before watching
        debounce_seconds: Wait time after file modification before processing
    """
    watcher = PDFWatcher(
        watch_dir=watch_dir,
        debounce_seconds=debounce_seconds,
    )

    watcher.run(scan_on_start=scan_on_start, run_forever=True)


if __name__ == "__main__":
    # Default: watch D_colect directory
    import sys

    watch_dir = sys.argv[1] if len(sys.argv) > 1 else "user_resources/D_colect"

    print(f"Starting PDF watcher for: {watch_dir}")
    watch_directory(watch_dir)
