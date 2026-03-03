"""NHO-PD brand color palette and layout constants for PPTX exports."""

from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# ── Slide dimensions (widescreen 16:9) ────────────────────────────────────
SLIDE_WIDTH = Inches(13.33)
SLIDE_HEIGHT = Inches(7.5)

# ── Brand colors ──────────────────────────────────────────────────────────
NAVY        = RGBColor(0x0D, 0x1B, 0x3E)   # Cover background
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GREY  = RGBColor(0xF5, 0xF5, 0xF7)   # Alternating table rows
AMBER       = RGBColor(0xE8, 0xA8, 0x20)   # Accent / highlight
TEXT_DARK   = RGBColor(0x1A, 0x1A, 0x2E)
TEXT_MUTED  = RGBColor(0x6B, 0x7B, 0x8D)
GREEN       = RGBColor(0x27, 0xAE, 0x60)
RED         = RGBColor(0xC0, 0x39, 0x2B)
BLUE        = RGBColor(0x27, 0x6E, 0xBF)

# Grade-specific colors (residential grades)
GRADE_COLORS: dict[str, RGBColor] = {
    "SL":    RGBColor(0xD4, 0xAF, 0x37),   # Gold
    "L":     RGBColor(0x6A, 0x0D, 0xAD),   # Purple
    "H-I":   RGBColor(0xC0, 0x39, 0x2B),   # Dark red
    "H-II":  RGBColor(0xE7, 0x4C, 0x3C),   # Red
    "M-I":   RGBColor(0x27, 0x6E, 0xBF),   # Blue
    "M-II":  RGBColor(0x3A, 0x9A, 0xD9),   # Mid blue
    "M-III": RGBColor(0x74, 0xB9, 0xFF),   # Light blue
    "A-I":   RGBColor(0x27, 0xAE, 0x60),   # Green
    "A-II":  RGBColor(0x82, 0xE0, 0xAA),   # Light green
}

# Office grades
OFFICE_GRADE_COLORS: dict[str, RGBColor] = {
    "A":  RGBColor(0xD4, 0xAF, 0x37),
    "B+": RGBColor(0x27, 0x6E, 0xBF),
    "B":  RGBColor(0x3A, 0x9A, 0xD9),
    "C":  RGBColor(0x74, 0xB9, 0xFF),
}

# KPI badge colors
KPI_COLORS: dict[str, RGBColor] = {
    "green": GREEN,
    "red":   RED,
    "amber": AMBER,
    "blue":  BLUE,
}

# Verdict badge colors
VERDICT_COLORS: dict[str, RGBColor] = {
    "green": GREEN,
    "amber": AMBER,
    "red":   RED,
}

# ── Layout constants ───────────────────────────────────────────────────────
MARGIN_LEFT     = Inches(0.5)
MARGIN_RIGHT    = Inches(0.5)
CONTENT_WIDTH   = Inches(12.33)
HEADER_HEIGHT   = Inches(1.1)
CONTENT_TOP     = Inches(1.6)
CONTENT_HEIGHT  = Inches(5.55)

# Header rule line
RULE_TOP        = Inches(1.05)
RULE_HEIGHT     = Inches(0.04)

# ── Typography ─────────────────────────────────────────────────────────────
FONT_NAME   = "Calibri"

FONT_COVER_TITLE    = Pt(36)
FONT_COVER_SUBTITLE = Pt(20)
FONT_SLIDE_TITLE    = Pt(22)
FONT_BODY           = Pt(11)
FONT_CAPTION        = Pt(10)
FONT_TABLE_HEADER   = Pt(10)
FONT_TABLE_BODY     = Pt(9)
FONT_KPI_VALUE      = Pt(28)
FONT_KPI_LABEL      = Pt(10)
FONT_BADGE          = Pt(14)
