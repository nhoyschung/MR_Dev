"""Abstract base extractor: read source text, split by pages/projects, write JSON."""

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseExtractor(ABC):
    """Base class for all data extractors."""

    PAGE_PATTERN = re.compile(r"^---\s*Page\s+(\d+)\s*---$", re.MULTILINE)

    def __init__(self, source_dir: Path, output_dir: Path) -> None:
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def read_source(self, filename: str) -> str:
        """Read a source text file and return its content."""
        path = self.source_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")
        return path.read_text(encoding="utf-8")

    def split_by_pages(self, text: str) -> dict[int, str]:
        """Split text into pages using '--- Page N ---' markers.

        Returns {page_number: page_content}.
        """
        pages: dict[int, str] = {}
        splits = self.PAGE_PATTERN.split(text)
        # splits alternates: [before_first_page, page_num, content, page_num, content, ...]
        for i in range(1, len(splits), 2):
            page_num = int(splits[i])
            content = splits[i + 1] if i + 1 < len(splits) else ""
            pages[page_num] = content.strip()
        return pages

    def split_by_projects(
        self, text: str, pattern: re.Pattern[str]
    ) -> list[dict[str, Any]]:
        """Split text into project sections using a header pattern.

        The pattern must have a named group 'name' (and optionally 'number').
        Returns list of {'number': str, 'name': str, 'content': str}.
        """
        sections: list[dict[str, Any]] = []
        matches = list(pattern.finditer(text))

        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            sections.append({
                "number": match.group("number") if "number" in match.groupdict() else str(i + 1),
                "name": match.group("name").strip(),
                "content": content,
            })
        return sections

    def write_json(self, filename: str, data: list[dict[str, Any]]) -> Path:
        """Write extracted data to a JSON file in the output directory."""
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def add_meta(
        self,
        record: dict[str, Any],
        source_file: str,
        page: int | None = None,
        confidence: float = 0.8,
    ) -> dict[str, Any]:
        """Add _meta tracking info to an extracted record."""
        record["_meta"] = {
            "source_file": source_file,
            "page": page,
            "confidence": confidence,
        }
        return record

    @abstractmethod
    def extract(self) -> dict[str, int]:
        """Run extraction. Returns {output_file: record_count}."""
        ...
