"""Common utilities for CLI commands."""

import sys
from datetime import datetime, timezone
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


def print_header(text: str):
    """Print colored header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}", file=sys.stderr)


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def print_section(title: str):
    """Print section title."""
    print(f"\n{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{'-'*len(title)}")


def format_size(size_mb: float) -> str:
    """Format file size for display."""
    if size_mb < 0.1:
        return f"{size_mb * 1024:.1f} KB"
    elif size_mb < 1024:
        return f"{size_mb:.1f} MB"
    else:
        return f"{size_mb / 1024:.1f} GB"


def format_duration(seconds: float) -> str:
    """Format duration for display."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def format_timestamp(dt: Optional[datetime]) -> str:
    """Format timestamp for display."""
    if dt is None:
        return "N/A"

    # If timezone-aware, convert to local
    if dt.tzinfo is not None:
        dt = dt.astimezone()

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def confirm_action(prompt: str, default: bool = False) -> bool:
    """Ask user for confirmation.

    Args:
        prompt: Question to ask
        default: Default answer if user presses Enter

    Returns:
        True if confirmed, False otherwise
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ['y', 'yes']


def print_table(headers: list[str], rows: list[list], column_widths: Optional[list[int]] = None):
    """Print formatted table.

    Args:
        headers: Column headers
        rows: Data rows
        column_widths: Optional fixed column widths
    """
    if not rows:
        print("(No data)")
        return

    # Calculate column widths if not provided
    if column_widths is None:
        column_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            column_widths.append(max_width + 2)

    # Print header
    header_line = "".join(h.ljust(w) for h, w in zip(headers, column_widths))
    print(f"{Colors.BOLD}{header_line}{Colors.RESET}")
    print("-" * sum(column_widths))

    # Print rows
    for row in rows:
        row_line = "".join(str(cell).ljust(w) for cell, w in zip(row, column_widths))
        print(row_line)


class ProgressBar:
    """Simple progress bar for terminal."""

    def __init__(self, total: int, width: int = 50, show_percent: bool = True):
        """Initialize progress bar.

        Args:
            total: Total number of items
            width: Width of progress bar in characters
            show_percent: Whether to show percentage
        """
        self.total = total
        self.width = width
        self.show_percent = show_percent
        self.current = 0

    def update(self, current: int, text: str = ""):
        """Update progress bar.

        Args:
            current: Current progress count
            text: Optional status text
        """
        self.current = current

        if self.total == 0:
            percent = 100
        else:
            percent = int((current / self.total) * 100)

        filled = int((current / self.total) * self.width) if self.total > 0 else self.width
        bar = "█" * filled + "░" * (self.width - filled)

        if self.show_percent:
            output = f"\r[{bar}] {percent}% ({current}/{self.total})"
        else:
            output = f"\r[{bar}] {current}/{self.total}"

        if text:
            output += f" - {text}"

        print(output, end="", flush=True)

    def finish(self, text: str = "Complete"):
        """Finish progress bar.

        Args:
            text: Completion message
        """
        self.update(self.total, text)
        print()  # New line


def print_summary_box(title: str, items: dict[str, str]):
    """Print summary box with key-value pairs.

    Args:
        title: Box title
        items: Dictionary of label-value pairs
    """
    max_label_len = max(len(label) for label in items.keys())

    print(f"\n{Colors.BOLD}{title}{Colors.RESET}")
    print("┌" + "─" * 78 + "┐")

    for label, value in items.items():
        padded_label = label.ljust(max_label_len)
        print(f"│ {Colors.BOLD}{padded_label}{Colors.RESET}: {value:<{76 - max_label_len - 2}} │")

    print("└" + "─" * 78 + "┘")
