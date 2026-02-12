"""Application configuration: paths, database URL, constants."""

from pathlib import Path

# Root directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
USER_RESOURCES_DIR = PROJECT_ROOT / "user_resources"

# Database
DB_PATH = DATA_DIR / "mr_system.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SEED_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Constants
REGIONS = ("South", "North", "Central")
DISTRICT_TYPES = ("urban", "suburban")
PROJECT_TYPES = ("apartment", "townhouse", "villa", "mixed-use", "commercial")
PROJECT_STATUSES = ("planning", "under-construction", "completed", "selling")
UNIT_TYPES = ("studio", "1BR", "2BR", "3BR", "4BR", "penthouse", "duplex",
              "officetel", "shophouse", "villa")
SEGMENTS = ("super-luxury", "luxury", "high-end", "mid-end", "affordable")
REPORT_TYPES = ("market_analysis", "price_analysis", "land_review",
                "case_study", "developer_analysis", "development_proposal")
HALF_PERIODS = ("H1", "H2")
FACTOR_TYPES = ("increase", "decrease")
FACTOR_CATEGORIES = (
    "location", "supply_shortage", "construction", "urban_planning",
    "competitive_price", "neighborhood", "old_project", "legal",
    "bank_loan", "oversupply", "management", "other",
)
FACILITY_TYPES = (
    "pool", "gym", "park", "commercial", "school", "hospital",
    "playground", "clubhouse", "security", "parking",
)
SALES_POINT_CATEGORIES = ("location", "design", "facility", "pricing", "developer")
COMPARISON_DIMENSIONS = (
    "location", "transportation", "surroundings", "design", "facilities",
    "unit_layout", "pricing", "developer_brand", "payment_terms",
    "legal_status", "management",
)
METRIC_TYPES = ("avg_price", "supply_count", "absorption", "new_launches",
                "avg_price_change_pct")
