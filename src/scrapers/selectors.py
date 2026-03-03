"""CSS selector registry for batdongsan.com.vn pages.

Selectors are grouped by page type. Update these when the site's
HTML structure changes.

Last verified: 2026-02-16
"""


class ProjectListSelectors:
    """Selectors for the project listing page (search results)."""

    # Container for each project card in search results
    CARD = "div.js__card"
    # Project name — premium cards use <span>, regular cards use <h3>
    CARD_TITLE = "span.js__card-title, h3.js__card-title"
    # Price info on card
    CARD_PRICE = "span.re__card-config-price"
    # Area info on card (may have leading "·")
    CARD_AREA = "span.re__card-config-area"
    # Location info (district, city)
    CARD_LOCATION = "div.re__card-location"
    # Main card link wrapping the whole card
    CARD_LINK = "a.js__product-link-for-product-id"
    # Pagination next button (last icon link)
    PAGINATION_NEXT = "a.re__pagination-icon"
    # Pagination container
    PAGINATION = "div.re__pagination"
    # Bedroom count
    CARD_BEDROOMS = "span.re__card-config-bedroom"
    # Bathroom count (not always present)
    CARD_BATHROOMS = "span.re__card-config-toilet"
    # Description snippet
    CARD_DESCRIPTION = "div.re__card-description"


class ProjectDetailSelectors:
    """Selectors for individual project detail pages."""

    # Project title
    TITLE = "h1.re__pr-title, h1.js__pr-title"
    # Developer name
    DEVELOPER = "div.re__pr-short-info-item >> text=Chủ đầu tư"
    # Address / location
    ADDRESS = "span.re__pr-short-description--address"
    # Price range
    PRICE_RANGE = "div.re__pr-short-info-item >> text=Mức giá"
    # Total units
    TOTAL_UNITS = "div.re__pr-short-info-item >> text=Số căn hộ"
    # Completion date
    COMPLETION = "div.re__pr-short-info-item >> text=Năm bàn giao"
    # Project overview section
    OVERVIEW_SECTION = "div.re__pr-overview"
    # Amenities / facilities list
    AMENITIES = "div.re__pr-amenity-item"
    # Project type
    PROJECT_TYPE = "div.re__pr-short-info-item >> text=Loại hình"
    # Project status
    STATUS = "div.re__pr-short-info-item >> text=Tình trạng"
    # Short info items (generic)
    SHORT_INFO_ITEM = "div.re__pr-short-info-item"


class OfficeListingSelectors:
    """Selectors for office lease listing pages on batdongsan.com.vn.

    The card structure is the same as residential; we reuse ProjectListSelectors
    for card-level parsing. These selectors cover office-specific detail fields.
    """

    # Reuse the residential card selectors for the list page
    CARD = "div.js__card"
    CARD_TITLE = "span.js__card-title, h3.js__card-title"
    CARD_PRICE = "span.re__card-config-price"
    CARD_AREA = "span.re__card-config-area"
    CARD_LOCATION = "div.re__card-location"
    CARD_LINK = "a.js__product-link-for-product-id"
    PAGINATION_NEXT = "a.re__pagination-icon"

    # Detail page — office specific
    TITLE = "h1.re__pr-title, h1.js__pr-title"
    PRICE = "span.re__pr-short-description--price"
    AREA = "span.re__pr-short-description--area"
    ADDRESS = "span.re__pr-short-description--address"
    SPEC_TABLE = "div.re__pr-specs-content-item"
    SPEC_LABEL = "span.re__pr-specs-content-item-title"
    SPEC_VALUE = "span.re__pr-specs-content-item-value"


class ListingDetailSelectors:
    """Selectors for individual listing (unit) pages."""

    # Listing title
    TITLE = "h1.re__pr-title"
    # Price display
    PRICE = "span.re__pr-short-description--price"
    # Area
    AREA = "span.re__pr-short-description--area"
    # Specification table rows
    SPEC_TABLE = "div.re__pr-specs-content-item"
    SPEC_LABEL = "span.re__pr-specs-content-item-title"
    SPEC_VALUE = "span.re__pr-specs-content-item-value"
    # Direction/facing
    DIRECTION = "div.re__pr-specs-content-item >> text=Hướng"
    # Floor
    FLOOR = "div.re__pr-specs-content-item >> text=Số tầng"
    # Bedrooms
    BEDROOMS = "div.re__pr-specs-content-item >> text=Số phòng ngủ"
    # Bathrooms
    BATHROOMS = "div.re__pr-specs-content-item >> text=Số toilet"
    # Project reference link
    PROJECT_LINK = "a.re__link-se >> text=Thuộc dự án"
