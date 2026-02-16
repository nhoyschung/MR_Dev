"""Fuzzy-match extracted project names to database project IDs."""

import re
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import Project


# Names that are section headers, column headers, or other non-project text
_JUNK_NAMES: set[str] = {
    # Section headers
    "on-sales projects", "on sales projects", "new launch projects",
    "future launch projects", "completed projects", "zone i", "zone ii",
    "zone iii", "zone iv", "i. zone i", "ii. zone ii", "iii. zone iii",
    "ii. on-sales projects", "iii. zone i", "remarkable",
    "remarable projects", "analyzed projects",
    # Column headers
    "project name", "unit type", "location", "developer", "grade",
    "price", "status", "block", "type", "area", "items", "level",
    "description", "development", "facilities", "operation",
    "total units", "sales point", "sales status", "apartment",
    "unit finishing", "unit layout", "unit ratio", "merging",
    # City/district names used as headers
    "ho chi minh city", "hanoi", "binh duong", "hcmc", "ha noi",
    "da nang", "hai phong", "ha long", "dong anh", "tan uyen",
    # Generic labels
    "penthouse", "duplex", "shophouse", "landed house", "block b2",
    "merging information", "market situation", "n/a",
    # Layout/plan labels
    "master plan", "master plan & circulation", "typical floor",
    "typical floor plan", "typical unit layout", "project map",
    "project evaluation", "payment schedule", "public facility",
    "key characteristics", "co-operation strategy", "for customer",
    "highlighted features", "open-space concept with dual balcony",
    "section & product distribution", "section & product type distribution",
    # Grade codes
    "h-i", "h-ii", "m-i", "m-ii", "m-iii", "a-i", "a-ii", "sl", "l",
    # Other noise
    "i & ii", "hawaii", "rr2.5", "vhop1", "symlife",
    "dong nai river", "saigon river",
    # Timeline/developer company names (not projects)
    "complex development timeline (2018-2024)", "lideco",
}

# Patterns indicating junk names (matched as regex)
_JUNK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^[IVX]+\.\s", re.IGNORECASE),   # Roman numeral section headers
    re.compile(r"^\d+\.\d+\s", re.IGNORECASE),    # Numbered section headers like "02.01"
    re.compile(r"^ANALYZED\s+PROJECTS\s*\(", re.IGNORECASE),  # "ANALYZED PROJECTS (10)"
    re.compile(r"^C\s+O\s+N\s+F\s+I", re.IGNORECASE),  # Spaced-out "CONFIDENTIAL"
    re.compile(r"TIMELINE\s*\(\d{4}", re.IGNORECASE),  # "TIMELINE (2018-2024)"
    re.compile(r"^OVERALL\s+IN\s+\d{4}", re.IGNORECASE),  # "OVERALL IN 2024-2025"
    re.compile(r"^HIGHLIGHTED\s+FEATURES\s+IN", re.IGNORECASE),  # "HIGHLIGHTED FEATURES IN ZONE X"
    re.compile(r"^(?:LOW|HIGH)-RISE\s*\(", re.IGNORECASE),  # "LOW-RISE (H7-H10-H11)"
    re.compile(r"^BLOCK\s+[A-Z]\d", re.IGNORECASE),  # "BLOCK T3"
    re.compile(r"^TOWER\s+\w+$", re.IGNORECASE),  # "TOWER K8E"
    re.compile(r"^WONDERFUL\s+PARK$", re.IGNORECASE),  # "WONDERFUL PARK" (generic label)
    re.compile(r"DEVELOPMENT\s+TIMELINE", re.IGNORECASE),  # "COMPLEX DEVELOPMENT TIMELINE"
]


class ProjectMatcher:
    """Match extracted project names to existing DB projects.

    Uses 4-tier matching:
    1. Exact (case-insensitive)
    2. Alias (static mapping for known variants, confidence 0.95)
    3. Normalized (strip phase/block suffixes, punctuation)
    4. Substring (longest matching project name)
    """

    # NHO-PD internal code prefixes to strip
    PREFIX_PATTERN = re.compile(
        r"^(?:VHOP\s*\d*|VHGG|VHSC)\s*[-–—]\s*",
        re.IGNORECASE,
    )

    # Single-letter prefix like "A. ", "B. ", "G. " used in report labeling
    LETTER_PREFIX_PATTERN = re.compile(
        r"^[A-Z]\.\s+",
    )

    # Patterns to strip for normalized matching
    # This version consumes trailing names after phase suffixes (only after dashes)
    PHASE_PATTERN = re.compile(
        r"\s*[-–—]\s*\(?P\d+\)?\s+(?:Block|Tower)\s+\w[\w&]*"  # – (P1) Block B1&2
        r"|\s*[-–—]\s*\(?P\d+\)?\s+\S+"                        # – (P2) SKYZEN (dash + phase + trailing name)
        r"|\s*[-–—]\s*\(?P\d+\)?"                               # – (P1), - P2
        r"|\s*\(P\d+\)\s*"                                      # (P1) standalone — no trailing word consumed
        r"|\s*Phase\s+\d+"                                       # Phase 1
        r"|\s*[-–—]\s*Block\s+\w+"                               # – Block A
        , re.IGNORECASE
    )

    def __init__(
        self, session: Session, aliases: dict[str, str] | None = None
    ) -> None:
        self.session = session
        self._aliases = aliases or {}
        self._cache: dict[str, tuple[int, str]] = {}  # normalized_name -> (id, name)
        self._name_to_id: dict[str, int] = {}  # lowercase db_name -> id
        self._load_projects()

    def _load_projects(self) -> None:
        """Load all projects from DB into the match cache."""
        projects = self.session.query(Project).all()
        for p in projects:
            key = self._normalize(p.name)
            self._cache[key] = (p.id, p.name)
            self._name_to_id[p.name.lower()] = p.id

    @staticmethod
    def is_junk_name(name: str) -> bool:
        """Return True if the name is a section header, column header, or non-project text."""
        cleaned = name.strip()
        if not cleaned or len(cleaned) < 3:
            return True
        lower = cleaned.lower()
        if lower in _JUNK_NAMES:
            return True
        for pat in _JUNK_PATTERNS:
            if pat.match(cleaned):
                return True
        return False

    @staticmethod
    def _normalize(name: str) -> str:
        """Normalize a project name for matching."""
        # Replace Unicode dashes with ASCII hyphen first
        name = name.replace("\u2013", "-").replace("\u2014", "-")
        # Strip single-letter prefixes like "A. ", "B. "
        name = ProjectMatcher.LETTER_PREFIX_PATTERN.sub("", name)
        # Strip NHO-PD code prefixes (VHOP, VHGG, VHSC)
        name = ProjectMatcher.PREFIX_PATTERN.sub("", name)
        # Remove phase/block suffixes (including trailing names)
        name = ProjectMatcher.PHASE_PATTERN.sub("", name)
        # Remove parenthetical content
        name = re.sub(r"\([^)]*\)", "", name)
        # Strip trailing dashes and whitespace
        name = re.sub(r"\s*[-–—]\s*$", "", name)
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

        # Reject junk names immediately
        if self.is_junk_name(extracted_name):
            return None, 0.0

        # Tier 1: Exact match (case-insensitive)
        lower = extracted_name.strip().lower()
        for norm_key, (pid, db_name) in self._cache.items():
            if lower == db_name.lower():
                return pid, 1.0

        # Tier 2: Alias match
        alias_result = self._try_alias(extracted_name)
        if alias_result:
            return alias_result

        # Tier 3: Normalized match
        norm_input = self._normalize(extracted_name)
        if norm_input in self._cache:
            return self._cache[norm_input][0], 0.9

        # Tier 4: Substring match (find longest DB name contained in input, or vice versa)
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

    def _try_alias(self, extracted_name: str) -> Optional[tuple[int, float]]:
        """Try matching via the alias map. Returns (project_id, 0.95) or None."""
        if not self._aliases:
            return None
        # Try the raw name, normalized name, and uppercased name
        candidates = [
            extracted_name.strip(),
            self._normalize(extracted_name),
        ]
        for candidate in candidates:
            for alias_key, canonical_name in self._aliases.items():
                if (candidate.lower() == alias_key.lower()
                        or self._normalize(alias_key) == self._normalize(candidate)):
                    pid = self._name_to_id.get(canonical_name.lower())
                    if pid is not None:
                        return pid, 0.95
        return None
