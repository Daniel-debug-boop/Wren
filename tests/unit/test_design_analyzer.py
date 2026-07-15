"""Tests for the design analyzer."""

from __future__ import annotations

import asyncio

import pytest

from wren.app_server.design_analyzer import (
    DesignAnalyzer,
    DesignReport,
    ColorInfo,
    TypographyInfo,
    SpacingInfo,
    _hex_to_rgb,
    _classify_color_role,
    _closest_spacing_scale,
)


class TestHexToRgb:
    def test_white(self):
        assert _hex_to_rgb('#ffffff') == (255, 255, 255)

    def test_black(self):
        assert _hex_to_rgb('#000000') == (0, 0, 0)

    def test_without_hash(self):
        assert _hex_to_rgb('ff0000') == (255, 0, 0)

    def test_mixed_case(self):
        assert _hex_to_rgb('#AbCdEf') == (171, 205, 239)


class TestClassifyColorRole:
    def test_white_is_background(self):
        assert _classify_color_role('#ffffff') == 'background'

    def test_black_is_text(self):
        assert _classify_color_role('#000000') == 'text'

    def test_bright_gray_is_background(self):
        assert _classify_color_role('#f0f0f0') == 'background'

    def test_dark_gray_is_text(self):
        assert _classify_color_role('#1a1a1a') == 'text'

    def test_saturated_color_is_accent(self):
        assert _classify_color_role('#ff0000') == 'accent'

    def test_low_saturation_is_border(self):
        assert _classify_color_role('#cccccc') == 'border'


class TestClosestSpacingScale:
    def test_exact_8px(self):
        assert _closest_spacing_scale(8) == 1

    def test_exact_16px(self):
        assert _closest_spacing_scale(16) == 2

    def test_near_8px(self):
        assert _closest_spacing_scale(9) == 1

    def test_off_grid(self):
        assert _closest_spacing_scale(13) is None

    def test_zero(self):
        assert _closest_spacing_scale(0) == 0


class TestDesignAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return DesignAnalyzer()

    def test_analyze_css_colors(self, analyzer):
        css = """
        :root {
            --bg: #ffffff;
            --text: #1a1a2e;
            --primary: #6c63ff;
        }
        """
        report = asyncio.run(analyzer.analyze_css(css))
        assert len(report.colors) >= 3
        hexes = [c.hex for c in report.colors]
        assert '#ffffff' in hexes
        assert '#1a1a2e' in hexes
        assert '#6c63ff' in hexes

    def test_analyze_css_typography(self, analyzer):
        css = """
        .title { font-size: 24px; font-weight: 700; }
        .body { font-size: 16px; font-weight: 400; }
        """
        report = asyncio.run(analyzer.analyze_css(css))
        assert len(report.typography) >= 2
        sizes = [t.font_size for t in report.typography]
        assert 24 in sizes
        assert 16 in sizes

    def test_analyze_css_spacing(self, analyzer):
        css = """
        .card { padding: 16px; margin: 8px; gap: 24px; }
        """
        report = asyncio.run(analyzer.analyze_css(css))
        assert len(report.spacing) >= 2
        values = [s.value for s in report.spacing]
        assert 16 in values
        assert 8 in values

    def test_analyze_css_border_radius(self, analyzer):
        css = """
        .card { border-radius: 8px; }
        .button { border-radius: 4px; }
        """
        report = asyncio.run(analyzer.analyze_css(css))
        assert 8 in report.border_radius
        assert 4 in report.border_radius

    def test_analyze_css_shadows(self, analyzer):
        css = """
        .card { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        """
        report = asyncio.run(analyzer.analyze_css(css))
        assert len(report.shadows) >= 1

    def test_analyze_empty_css(self, analyzer):
        report = asyncio.run(analyzer.analyze_css(''))
        assert report.colors == []
        assert report.typography == []
        assert report.spacing == []

    def test_score_perfect(self, analyzer):
        css = """
        :root { --bg: #fff; --text: #000; }
        .card { padding: 16px; font-size: 16px; border-radius: 8px; }
        """
        report = asyncio.run(analyzer.analyze_css(css))
        assert report.score >= 80

    def test_score_penalizes_many_colors(self, analyzer):
        css = """
        .a { color: #111111; }
        .b { color: #222222; }
        .c { color: #333333; }
        .d { color: #444444; }
        .e { color: #555555; }
        .f { color: #666666; }
        .g { color: #777777; }
        .h { color: #888888; }
        .i { color: #999999; }
        .j { color: #aaaaaa; }
        .k { color: #bbbbbb; }
        .l { color: #cccccc; }
        """
        report = asyncio.run(analyzer.analyze_css(css))
        assert report.score < 100
        assert any('color' in i.lower() for i in report.issues)

    def test_issues_off_grid_spacing(self, analyzer):
        css = """
        .card { padding: 13px; margin: 7px; }
        """
        report = asyncio.run(analyzer.analyze_css(css))
        assert any('grid' in i.lower() for i in report.issues)

    def test_report_dataclass(self):
        report = DesignReport()
        assert report.colors == []
        assert report.typography == []
        assert report.spacing == []
        assert report.border_radius == []
        assert report.shadows == []
        assert report.score == 0.0
        assert report.issues == []
