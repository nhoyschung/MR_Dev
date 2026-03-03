"""PptxBuilder — layout engine that turns SlideContentManifest into .pptx files.

All text comes from the content JSON; the builder handles layout and styling only.
Language-agnostic: the same build path is used for EN and KO content.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from src.reports.pptx.theme import (
    SLIDE_WIDTH, SLIDE_HEIGHT,
    NAVY, WHITE, LIGHT_GREY, AMBER, TEXT_DARK, TEXT_MUTED, GREEN, RED, BLUE,
    GRADE_COLORS, KPI_COLORS, VERDICT_COLORS,
    MARGIN_LEFT, CONTENT_WIDTH, HEADER_HEIGHT, CONTENT_TOP, CONTENT_HEIGHT,
    RULE_TOP, RULE_HEIGHT,
    FONT_NAME,
    FONT_COVER_TITLE, FONT_COVER_SUBTITLE, FONT_SLIDE_TITLE,
    FONT_BODY, FONT_CAPTION, FONT_TABLE_HEADER, FONT_TABLE_BODY,
    FONT_KPI_VALUE, FONT_KPI_LABEL, FONT_BADGE,
)
from src.reports.pptx.content_schema import (
    CoverSlide, KpiDashboardSlide, TableSlide, ChartSlide,
    SwotSlide, ConclusionSlide, SectionDividerSlide, SlideContentManifest,
)


# ── Internal helpers ───────────────────────────────────────────────────────

def _set_font(run, size: Pt, bold: bool = False, color: Optional[RGBColor] = None,
              italic: bool = False) -> None:
    run.font.name = FONT_NAME
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color


def _add_textbox(
    slide,
    left: Emu, top: Emu, width: Emu, height: Emu,
    text: str,
    size: Pt = Pt(11),
    bold: bool = False,
    color: Optional[RGBColor] = None,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    italic: bool = False,
    word_wrap: bool = True,
) -> Any:
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    _set_font(run, size, bold, color, italic)
    return txBox


def _add_rect(slide, left: Emu, top: Emu, width: Emu, height: Emu,
              fill_color: RGBColor, line_color: Optional[RGBColor] = None) -> Any:
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape


def _add_slide_header(slide, title: str) -> None:
    """Add navy header bar with white title + amber accent rule."""
    # Header background
    _add_rect(slide, MARGIN_LEFT, Inches(0.2), CONTENT_WIDTH, HEADER_HEIGHT, NAVY)
    # Title text
    _add_textbox(
        slide,
        MARGIN_LEFT + Inches(0.25), Inches(0.3),
        CONTENT_WIDTH - Inches(0.5), HEADER_HEIGHT - Inches(0.1),
        title,
        size=FONT_SLIDE_TITLE, bold=True, color=WHITE,
    )
    # Amber accent rule below header
    _add_rect(slide, MARGIN_LEFT, RULE_TOP, CONTENT_WIDTH, RULE_HEIGHT, AMBER)


# ── PptxBuilder ───────────────────────────────────────────────────────────

class PptxBuilder:
    """Build NHO-PD-styled PPTX presentations from SlideContentManifest data."""

    def __init__(self) -> None:
        self._prs = Presentation()
        self._prs.slide_width = SLIDE_WIDTH
        self._prs.slide_height = SLIDE_HEIGHT
        # Use blank layout (index 6) for full control
        self._blank_layout = self._prs.slide_layouts[6]

    # ── Public slide-add methods (all return self for chaining) ────────────

    def add_cover(self, slide: CoverSlide) -> "PptxBuilder":
        """Full-bleed navy cover with title, subtitle, city, period, date."""
        s = self._prs.slides.add_slide(self._blank_layout)

        # Navy background
        _add_rect(s, Inches(0), Inches(0), SLIDE_WIDTH, SLIDE_HEIGHT, NAVY)

        # Amber accent strip (left edge)
        _add_rect(s, Inches(0), Inches(0), Inches(0.15), SLIDE_HEIGHT, AMBER)

        # Report type (small caps)
        _add_textbox(
            s,
            Inches(0.8), Inches(1.2), Inches(10), Inches(0.6),
            slide.get("report_type", "").upper(),
            size=Pt(13), bold=True, color=AMBER,
        )

        # Main title
        _add_textbox(
            s,
            Inches(0.8), Inches(1.9), Inches(11), Inches(1.8),
            slide.get("title", ""),
            size=FONT_COVER_TITLE, bold=True, color=WHITE,
        )

        # Subtitle
        _add_textbox(
            s,
            Inches(0.8), Inches(3.8), Inches(10), Inches(0.8),
            slide.get("subtitle", ""),
            size=FONT_COVER_SUBTITLE, color=RGBColor(0xCC, 0xCC, 0xCC),
        )

        # City | Period
        meta = f"{slide.get('city', '')}  ·  {slide.get('period', '')}"
        _add_textbox(
            s,
            Inches(0.8), Inches(4.8), Inches(8), Inches(0.5),
            meta,
            size=Pt(14), color=AMBER,
        )

        # Date (bottom right)
        _add_textbox(
            s,
            Inches(9), Inches(6.8), Inches(4), Inches(0.5),
            slide.get("date", ""),
            size=Pt(11), color=TEXT_MUTED, align=PP_ALIGN.RIGHT,
        )

        return self

    def add_section_divider(self, number: str, title: str, subtitle: str) -> "PptxBuilder":
        """Numbered section break slide (navy BG, large amber number)."""
        s = self._prs.slides.add_slide(self._blank_layout)

        _add_rect(s, Inches(0), Inches(0), SLIDE_WIDTH, SLIDE_HEIGHT, NAVY)
        _add_rect(s, Inches(0), Inches(0), Inches(0.15), SLIDE_HEIGHT, AMBER)

        _add_textbox(
            s,
            Inches(1), Inches(1.5), Inches(3), Inches(2.5),
            number,
            size=Pt(96), bold=True, color=AMBER,
        )
        _add_textbox(
            s,
            Inches(4.2), Inches(2.5), Inches(8.5), Inches(1.2),
            title,
            size=Pt(32), bold=True, color=WHITE,
        )
        _add_textbox(
            s,
            Inches(4.2), Inches(3.9), Inches(8.5), Inches(0.8),
            subtitle,
            size=Pt(16), color=RGBColor(0xCC, 0xCC, 0xCC),
        )

        return self

    def add_kpi_dashboard(self, slide: KpiDashboardSlide) -> "PptxBuilder":
        """KPI dashboard: up to 6 KPI tiles + expert narrative note."""
        s = self._prs.slides.add_slide(self._blank_layout)
        _add_slide_header(s, slide.get("slide_title", "Key Performance Indicators"))

        kpis = slide.get("kpis", [])
        n = min(len(kpis), 6)
        tile_w = Inches(2.0)
        tile_h = Inches(1.6)
        gap = Inches(0.18)
        start_left = MARGIN_LEFT
        top = CONTENT_TOP

        for i, kpi in enumerate(kpis[:n]):
            col = i % 3
            row = i // 3
            left = start_left + col * (tile_w + gap)
            t = top + row * (tile_h + gap)

            color = KPI_COLORS.get(kpi.get("color", "blue"), BLUE)

            # Tile background
            _add_rect(s, left, t, tile_w, tile_h, color)

            # Value
            _add_textbox(
                s, left + Inches(0.1), t + Inches(0.2),
                tile_w - Inches(0.2), Inches(0.8),
                kpi.get("value", ""),
                size=FONT_KPI_VALUE, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            )
            # Label
            _add_textbox(
                s, left + Inches(0.05), t + Inches(1.0),
                tile_w - Inches(0.1), Inches(0.35),
                kpi.get("label", ""),
                size=FONT_KPI_LABEL, color=WHITE, align=PP_ALIGN.CENTER,
            )
            # Delta
            if kpi.get("delta"):
                _add_textbox(
                    s, left + Inches(0.05), t + Inches(1.35),
                    tile_w - Inches(0.1), Inches(0.22),
                    kpi["delta"],
                    size=Pt(8), color=WHITE, align=PP_ALIGN.CENTER, italic=True,
                )

        # Expert note (right panel when 3 KPIs per row)
        note = slide.get("note", "")
        if note:
            note_left = start_left + 3 * (tile_w + gap) + Inches(0.3)
            note_width = CONTENT_WIDTH - (3 * (tile_w + gap)) - Inches(0.3)
            _add_textbox(
                s, note_left, top, note_width, CONTENT_HEIGHT,
                note,
                size=FONT_BODY, color=TEXT_DARK,
            )

        return self

    def add_table_slide(self, slide: TableSlide) -> "PptxBuilder":
        """Data table with alternating row shading and optional caption."""
        s = self._prs.slides.add_slide(self._blank_layout)
        _add_slide_header(s, slide.get("title", ""))

        headers = slide.get("headers", [])
        rows = slide.get("rows", [])
        caption = slide.get("caption", "")
        grade_col = slide.get("grade_col_index")

        if not headers:
            return self

        n_cols = len(headers)
        col_w = CONTENT_WIDTH / n_cols
        row_h = Inches(0.38)
        caption_reserve = Inches(0.8) if caption else Inches(0)
        table_h = CONTENT_HEIGHT - caption_reserve

        table = s.shapes.add_table(
            len(rows) + 1, n_cols,
            MARGIN_LEFT, CONTENT_TOP, CONTENT_WIDTH,
            min(table_h, row_h * (len(rows) + 1)),
        ).table

        # Header row
        for col_idx, header in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY
            tf = cell.text_frame
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = str(header)
            _set_font(run, FONT_TABLE_HEADER, bold=True, color=WHITE)

        # Data rows
        for row_idx, row in enumerate(rows):
            bg = LIGHT_GREY if row_idx % 2 == 0 else WHITE
            for col_idx, cell_val in enumerate(row[:n_cols]):
                cell = table.cell(row_idx + 1, col_idx)
                cell.fill.solid()
                # Grade column coloring
                if grade_col is not None and col_idx == grade_col:
                    grade_color = GRADE_COLORS.get(str(cell_val), bg)
                    cell.fill.fore_color.rgb = grade_color
                    txt_color = WHITE
                else:
                    cell.fill.fore_color.rgb = bg
                    txt_color = TEXT_DARK

                tf = cell.text_frame
                tf.paragraphs[0].alignment = PP_ALIGN.CENTER
                run = tf.paragraphs[0].add_run()
                run.text = str(cell_val) if cell_val is not None else ""
                _set_font(run, FONT_TABLE_BODY, color=txt_color)

        # Caption
        if caption:
            caption_top = CONTENT_TOP + table_h + Inches(0.05)
            _add_textbox(
                s, MARGIN_LEFT, caption_top, CONTENT_WIDTH, caption_reserve,
                caption,
                size=FONT_CAPTION, color=TEXT_MUTED, italic=True,
            )

        return self

    def add_chart_slide(self, slide: ChartSlide) -> "PptxBuilder":
        """Chart slide: renders matplotlib figure into slide image placeholder.

        Chart dispatch is dict-based for easy extension. Each entry maps
        chart_type → callable(params) → Optional[Figure].
        """
        from src.reports.charts import fig_to_bytesio
        import matplotlib.pyplot as plt

        s = self._prs.slides.add_slide(self._blank_layout)
        _add_slide_header(s, slide.get("title", ""))

        chart_type = slide.get("chart_type", "")
        params = slide.get("chart_params", {})
        right_text = slide.get("right_panel_text", "")
        caption = slide.get("caption", "")

        # Decide layout: chart only vs chart + right panel
        has_right = bool(right_text)
        chart_w = Inches(7.5) if has_right else CONTENT_WIDTH
        right_left = MARGIN_LEFT + chart_w + Inches(0.2)
        right_w = CONTENT_WIDTH - chart_w - Inches(0.2)

        # Build figure via dict dispatch
        fig = None
        try:
            chart_dispatch = self._get_chart_dispatch()
            factory = chart_dispatch.get(chart_type)
            if factory:
                fig = factory(params)

            if fig is not None:
                buf = fig_to_bytesio(fig)
                plt.close(fig)
                s.shapes.add_picture(
                    buf, MARGIN_LEFT, CONTENT_TOP, chart_w,
                    CONTENT_HEIGHT - (Inches(0.55) if caption else Inches(0)),
                )
        except Exception:
            # If chart fails, show error placeholder
            _add_textbox(
                s, MARGIN_LEFT, CONTENT_TOP, chart_w, Inches(1),
                f"[Chart unavailable: {chart_type}]",
                size=Pt(10), color=RED,
            )

        # Right panel text
        if has_right:
            _add_textbox(
                s, right_left, CONTENT_TOP, right_w, CONTENT_HEIGHT,
                right_text,
                size=FONT_BODY, color=TEXT_DARK,
            )

        # Caption below chart
        if caption:
            cap_top = CONTENT_TOP + CONTENT_HEIGHT - Inches(0.5)
            _add_textbox(
                s, MARGIN_LEFT, cap_top, chart_w, Inches(0.5),
                caption,
                size=FONT_CAPTION, color=TEXT_MUTED, italic=True,
            )

        return self

    @staticmethod
    def _get_chart_dispatch() -> dict:
        """Return chart_type → factory(params) dispatch dict.

        Lazy import to avoid circular deps. New chart types are added here.
        """
        from src.reports.charts import (
            create_grade_distribution_figure,
            create_radar_figure,
            create_price_trend_figure,
            create_supply_demand_figure,
            create_price_comparison_figure,
            create_unit_type_grouped_bar_figure,
            create_variance_comparison_figure,
            create_area_price_scatter_figure,
            create_phase_price_progression_figure,
            create_zone_product_mix_figure,
            create_competitor_distance_band_figure,
            create_competitor_unit_mix_figure,
            create_absorption_timeline_figure,
        )
        return {
            # Core charts
            "grade_distribution": lambda p: create_grade_distribution_figure(
                p.get("grade_data", [])
            ),
            "radar": lambda p: create_radar_figure(
                p.get("projects_scores", []), p.get("categories", [])
            ),
            "price_trend": lambda p: create_price_trend_figure(
                p.get("trend_data", [])
            ),
            "supply_demand": lambda p: create_supply_demand_figure(
                p.get("total_inventory", 0), p.get("new_supply", 0),
                p.get("sold_units", 0), p.get("remaining_inventory", 0),
                p.get("absorption_rate", 0.0),
            ),
            "price_comparison": lambda p: create_price_comparison_figure(
                p.get("zone_avg", 0), p.get("zone_min", 0),
                p.get("zone_max", 0), p.get("city_avg", 0),
                p.get("zone_name", "Zone"), p.get("city_name", "City"),
            ),
            # Unit-type analysis charts
            "unit_type_grouped_bar": lambda p: create_unit_type_grouped_bar_figure(
                p.get("projects_data", [])
            ),
            "variance_comparison": lambda p: create_variance_comparison_figure(
                p.get("variance_data", [])
            ),
            "area_price_scatter": lambda p: create_area_price_scatter_figure(
                p.get("scatter_data", [])
            ),
            # Land site / product proposal charts
            "phase_price_progression": lambda p: create_phase_price_progression_figure(
                p.get("phases_data", [])
            ),
            "zone_product_mix": lambda p: create_zone_product_mix_figure(
                p.get("zones_data", [])
            ),
            "competitor_distance_band": lambda p: create_competitor_distance_band_figure(
                p.get("competitors_data", [])
            ),
            "competitor_unit_mix": lambda p: create_competitor_unit_mix_figure(
                p.get("competitors_data", [])
            ),
            "absorption_timeline": lambda p: create_absorption_timeline_figure(
                p.get("absorption_data", [])
            ),
        }

    def add_swot_slide(self, slide: SwotSlide) -> "PptxBuilder":
        """2x2 SWOT quadrant layout."""
        s = self._prs.slides.add_slide(self._blank_layout)
        _add_slide_header(s, slide.get("title", "SWOT Analysis"))

        quadrants = [
            ("Strengths", slide.get("strengths", []), GREEN, Inches(0.5), CONTENT_TOP),
            ("Weaknesses", slide.get("weaknesses", []), RED, Inches(6.92), CONTENT_TOP),
            ("Opportunities", slide.get("opportunities", []), BLUE,
             Inches(0.5), CONTENT_TOP + Inches(2.8)),
            ("Threats", slide.get("threats", []), AMBER,
             Inches(6.92), CONTENT_TOP + Inches(2.8)),
        ]

        q_w = Inches(6.17)
        q_h = Inches(2.65)

        for label, items, color, left, top in quadrants:
            _add_rect(s, left, top, q_w, q_h, color)
            _add_textbox(
                s, left + Inches(0.15), top + Inches(0.1),
                q_w - Inches(0.3), Inches(0.35),
                label.upper(),
                size=Pt(11), bold=True, color=WHITE,
            )
            bullet_text = "\n".join(f"• {item}" for item in items[:4])
            _add_textbox(
                s, left + Inches(0.15), top + Inches(0.55),
                q_w - Inches(0.3), q_h - Inches(0.65),
                bullet_text,
                size=Pt(9), color=WHITE,
            )

        return self

    def add_conclusion_slide(self, slide: ConclusionSlide) -> "PptxBuilder":
        """Conclusion with verdict badge and key findings bullets."""
        s = self._prs.slides.add_slide(self._blank_layout)
        _add_slide_header(s, slide.get("title", "Conclusion"))

        verdict = slide.get("verdict", "")
        badge_label = slide.get("badge_label", verdict)
        badge_color_key = slide.get("badge_color", "green")
        badge_color = VERDICT_COLORS.get(badge_color_key, GREEN)

        # Large verdict badge
        _add_rect(s, MARGIN_LEFT, CONTENT_TOP, Inches(4.5), Inches(1.8), badge_color)
        _add_textbox(
            s, MARGIN_LEFT + Inches(0.15), CONTENT_TOP + Inches(0.4),
            Inches(4.2), Inches(1.0),
            badge_label,
            size=FONT_BADGE, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
        )

        # Bullets on the right
        bullets = slide.get("bullets", [])
        bullet_text = "\n".join(f"• {b}" for b in bullets[:5])
        _add_textbox(
            s, Inches(5.5), CONTENT_TOP, Inches(7.3), CONTENT_HEIGHT,
            bullet_text,
            size=FONT_BODY, color=TEXT_DARK,
        )

        return self

    def add_two_column_slide(
        self,
        title: str,
        left_title: str,
        left_content: str,
        right_title: str,
        right_content: str,
    ) -> "PptxBuilder":
        """Generic two-column text layout."""
        s = self._prs.slides.add_slide(self._blank_layout)
        _add_slide_header(s, title)

        col_w = CONTENT_WIDTH / 2 - Inches(0.1)
        right_left = MARGIN_LEFT + col_w + Inches(0.2)

        for left, heading, content in [
            (MARGIN_LEFT, left_title, left_content),
            (right_left, right_title, right_content),
        ]:
            _add_textbox(
                s, left, CONTENT_TOP, col_w, Inches(0.4),
                heading,
                size=Pt(12), bold=True, color=NAVY,
            )
            _add_textbox(
                s, left, CONTENT_TOP + Inches(0.45), col_w,
                CONTENT_HEIGHT - Inches(0.45),
                content,
                size=FONT_BODY, color=TEXT_DARK,
            )

        return self

    # ── build_from_manifest (primary entry point) ─────────────────────────

    def build_from_manifest(self, manifest: SlideContentManifest) -> "PptxBuilder":
        """Dispatch each slide in manifest to the correct add_* method.

        This is the single entry point used by both EN and KO pptx-builder agents.
        """
        dispatch = {
            "cover":           lambda s: self.add_cover(s),
            "kpi_dashboard":   lambda s: self.add_kpi_dashboard(s),
            "table":           lambda s: self.add_table_slide(s),
            "chart":           lambda s: self.add_chart_slide(s),
            "swot":            lambda s: self.add_swot_slide(s),
            "conclusion":      lambda s: self.add_conclusion_slide(s),
            "section_divider": lambda s: self.add_section_divider(
                s.get("number", ""), s.get("title", ""), s.get("subtitle", "")
            ),
        }

        for slide in manifest.get("slides", []):
            slide_type = slide.get("type", "")
            handler = dispatch.get(slide_type)
            if handler:
                handler(slide)

        return self

    # ── save ──────────────────────────────────────────────────────────────

    def save(self, output_path: Path) -> Path:
        """Save presentation to disk and return the path."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._prs.save(str(output_path))
        return output_path
