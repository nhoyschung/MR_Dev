"""Scraper configuration: URLs, delays, limits, user agents."""

# Base URLs
BDS_BASE_URL = "https://batdongsan.com.vn"
BDS_PROJECT_LIST_URL = BDS_BASE_URL + "/ban-can-ho-chung-cu-{city_slug}"
BDS_PROJECT_DETAIL_URL = BDS_BASE_URL + "/du-an/{project_slug}"
BDS_LISTING_SEARCH_URL = BDS_BASE_URL + "/ban-can-ho-chung-cu/{district_slug}"

# Office / commercial lease URLs
BDS_OFFICE_LEASE_URL = BDS_BASE_URL + "/cho-thue-van-phong-{city_slug}"

# City slug mapping
CITY_SLUGS = {
    "hcmc": "tp-hcm",
    "hanoi": "ha-noi",
    "binh_duong": "binh-duong",
    "da_nang": "da-nang",
}

# Rate limiting
DEFAULT_MIN_DELAY_SEC = 2.0
DEFAULT_MAX_DELAY_SEC = 5.0
MAX_REQUESTS_PER_MINUTE = 12
TOKEN_BUCKET_CAPACITY = 3  # Allow small bursts

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0  # Exponential backoff base in seconds

# Browser settings
PAGE_TIMEOUT_MS = 30_000
NAVIGATION_TIMEOUT_MS = 60_000
DEFAULT_VIEWPORT_WIDTH = 1366
DEFAULT_VIEWPORT_HEIGHT = 768
VIEWPORT_JITTER = 100  # +/- pixels for randomization

# User agent rotation pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

# Pagination
MAX_PAGES_PER_SCRAPE = 50
ITEMS_PER_PAGE = 20
