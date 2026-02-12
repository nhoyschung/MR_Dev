"""Fuzzy-match extracted project names to database project IDs."""

import re
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import Project


class ProjectMatcher:
    """Match extracted project names to existing DB projects.

    Uses 3-tier matching:
    1. Exact (case-insensitive)
    2. Normalized (strip phase/block suffixes, punctuation)
    3. Substring (longest matching project name)
    """

    # Patterns to strip for normalized matching
    PHASE_PATTERN = re.compile(
        r"\s*[-–—]\s*\(?P\d+\)?"  # – (P1), - P2
        r"|\s*\(P\d+\)\s*"        # (P1)
        r"|\s*Phase\s+\d+"        # Phase 1
        r"|\s*[-–—]\s*Block\s+\w+"  # – Block A
        r"|\s*[-–—]\s*\(?(?:P\d+)\)?\s+(?:Block|Tower)\s+\w+"  # (P1) Block B1&2
        , re.IGNORECASE
    )

    def __init__(self, session: Session) -> None:
        self.session = session
        self._cache: dict[str, tuple[int, str]] = {}  # normalized_name -> (id, name)
        self._load_projects()

    def _load_projects(self) -> None:
        """Load all projects from DB into the match cache."""
        projects = self.session.query(Project).all()
        for p in projects:
            key = self._normalize(p.name)
            self._cache[key] = (p.id, p.name)

    @staticmethod
    def _normalize(name: str) -> str:
        """Normalize a project name for matching."""
        # Remove phase/block suffixes
        name = ProjectMatcher.PHASE_PATTERN.sub("", name)
        # Remove parenthetical content
        name = re.sub(r"\([^)]*\)", "", name)
        # Collapse whitespace and lowercase
        name = re.sub(r"\s+", " ", name).strip().lower()
        # Remove punctuation except hyphens
        name = re.sub(r"[^\w\s-]", "", name)
        return name

    def match(self, extracted_name: str) -> tuple[Optional[int], float]:
        """Match an extracted name to a DB project.

        Returns (project_id, confidence) or (None, 0.0).
        """
        if not extracted_name:
            return None, 0.0

        # Tier 1: Exact match (case-insensitive)
        lower = extracted_name.strip().lower()
        for norm_key, (pid, db_name) in self._cache.items():
            if lower == db_name.lower():
                return pid, 1.0

        # Tier 2: Normalized match
        norm_input = self._normalize(extracted_name)
        if norm_input in self._cache:
            return self._cache[norm_input][0], 0.9

        # Tier 3: Substring match (find longest DB name contained in input, or vice versa)
        best_match: Optional[tuple[int, float]] = None
        best_len = 0
        for norm_key, (pid, db_name) in self._cache.items():
            db_lower = db_name.lower()
            if db_lower in lower or lower in db_lower:
                match_len = min(len(db_lower), len(lower))
                if match_len > best_len:
                    best_len = match_len
                    # Confidence based on length ratio
                    ratio = match_len / max(len(db_lower), len(lower))
                    best_match = (pid, round(0.5 + 0.3 * ratio, 2))

        if best_match:
            return best_match

        return None, 0.0
