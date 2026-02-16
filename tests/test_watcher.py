"""Tests for PDF file watcher."""

import time
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.collectors.watcher import PDFWatcher, PDFWatcherEventHandler
from src.collectors.orchestrator import IngestionOrchestrator


@pytest.fixture
def temp_watch_dir(tmp_path):
    """Create temporary watch directory."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    return watch_dir


@pytest.fixture
def temp_pdf(tmp_path):
    """Create temporary PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    # Create minimal valid PDF
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


def test_watcher_initialization(temp_watch_dir):
    """Test watcher initialization."""
    watcher = PDFWatcher(temp_watch_dir)

    assert watcher.watch_dir == temp_watch_dir
    assert watcher._running is False
    assert watcher.orchestrator is not None
    assert watcher.event_handler is not None
    assert watcher.observer is not None


def test_watcher_status(temp_watch_dir):
    """Test watcher status reporting."""
    watcher = PDFWatcher(temp_watch_dir)

    status = watcher.get_status()

    assert status["running"] is False
    assert status["watch_dir"] == str(temp_watch_dir)
    assert "extracted_text_dir" in status
    assert status["start_time"] is None


def test_watcher_start_stop(temp_watch_dir):
    """Test watcher start and stop."""
    watcher = PDFWatcher(temp_watch_dir)

    # Start watcher
    watcher.start()
    assert watcher._running is True
    assert watcher._start_time is not None

    # Stop watcher
    watcher.stop()
    assert watcher._running is False


def test_event_handler_pdf_filter():
    """Test that event handler only processes PDF files."""
    orchestrator = Mock(spec=IngestionOrchestrator)
    handler = PDFWatcherEventHandler(orchestrator)

    # Mock file creation event for non-PDF file
    from watchdog.events import FileCreatedEvent

    txt_event = FileCreatedEvent("test.txt")
    handler.on_created(txt_event)

    # Should not process non-PDF files
    assert "test.txt" not in handler._processing

    # Mock file creation event for PDF file
    pdf_event = FileCreatedEvent("test.pdf")

    # Mock the ingestion to avoid actual processing
    with patch.object(handler, '_schedule_ingestion') as mock_schedule:
        handler.on_created(pdf_event)
        mock_schedule.assert_called_once()


def test_event_handler_debounce():
    """Test event handler debouncing."""
    orchestrator = Mock(spec=IngestionOrchestrator)
    handler = PDFWatcherEventHandler(orchestrator, debounce_seconds=0.5)

    from watchdog.events import FileModifiedEvent

    pdf_path = "test.pdf"
    event = FileModifiedEvent(pdf_path)

    # First modification
    with patch.object(handler, '_schedule_ingestion') as mock_schedule:
        handler.on_modified(event)
        assert mock_schedule.call_count == 1

    # Second modification immediately after (should be debounced)
    with patch.object(handler, '_schedule_ingestion') as mock_schedule:
        handler.on_modified(event)
        assert mock_schedule.call_count == 0  # Debounced

    # Third modification after debounce period
    time.sleep(0.6)
    with patch.object(handler, '_schedule_ingestion') as mock_schedule:
        handler.on_modified(event)
        assert mock_schedule.call_count == 1  # Not debounced


def test_event_handler_callback():
    """Test callback function is called after successful ingestion."""
    orchestrator = Mock(spec=IngestionOrchestrator)
    callback = Mock()

    handler = PDFWatcherEventHandler(
        orchestrator,
        on_ingest_callback=callback
    )

    # Mock successful ingestion
    mock_report = Mock()
    mock_report.id = 1
    mock_report.filename = "test.pdf"
    mock_report.page_count = 10
    mock_report.quality_score = 0.5

    with patch('src.collectors.watcher.get_session') as mock_session:
        mock_session.return_value.__enter__.return_value = Mock()
        orchestrator.ingest_pdf.return_value = mock_report

        pdf_path = Path("test.pdf")
        handler._ingest_file(pdf_path)

        # Callback should be called with report
        callback.assert_called_once_with(mock_report)


def test_watcher_scan_on_start(temp_watch_dir, temp_pdf):
    """Test scan_on_start functionality."""
    # Copy test PDF to watch directory
    dest_pdf = temp_watch_dir / "test_report.pdf"
    shutil.copy(temp_pdf, dest_pdf)

    watcher = PDFWatcher(temp_watch_dir)

    # Mock orchestrator.scan_and_ingest
    with patch.object(watcher.orchestrator, 'scan_and_ingest') as mock_scan:
        mock_scan.return_value = {'success': 1, 'failed': 0, 'skipped': 0}

        # Run with scan_on_start=True, run_forever=False
        watcher.run(scan_on_start=True, run_forever=False)

        # Should have called scan_and_ingest
        mock_scan.assert_called_once()


def test_watcher_duplicate_prevention():
    """Test that watcher doesn't process same file twice concurrently."""
    orchestrator = Mock(spec=IngestionOrchestrator)
    handler = PDFWatcherEventHandler(orchestrator)

    pdf_path = Path("test.pdf")

    # Add file to processing set
    handler._processing.add(str(pdf_path))

    # Try to schedule ingestion
    with patch.object(handler, '_ingest_file') as mock_ingest:
        handler._schedule_ingestion(pdf_path)

        # Should not ingest because already processing
        mock_ingest.assert_not_called()
