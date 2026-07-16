"""Design Analyzer — background service for extracting design patterns.

Analyzes screenshots and UI components to extract:
- Color palettes (dominant colors, semantic usage)
- Typography patterns (font families, sizes, weights)
- Spacing rhythm (padding, margin, gap patterns)
- Border radius consistency
- Shadow depth patterns

Usage:
    from wren.app_server.design_analyzer import DesignAnalyzer

    analyzer = DesignAnalyzer()
    report = await analyzer.analyze_screenshot(path_to_screenshot)
    # report = {
    #     "colors": [...],
    #     "typography": [...],
    #     "spacing": [...],
    #     "border_radius": [...],
    #     "shadows": [...]
    # }
"""

from __future__ import annotations

import colorsys
import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ColorInfo:
    hex: str
    rgb: tuple[int, int, int]
    count: int
    percentage: float
    role: str  # 'background', 'text', 'accent', 'border', 'unknown'


@dataclass
class TypographyInfo:
    font_family: str
    font_size: int
    font_weight: int
    line_height: float | None = None
    count: int = 0


@dataclass
class SpacingInfo:
    value: int
    frequency: int
    scale_position: int | None = None  # position in 4px/8px grid


@dataclass
class DesignReport:
    colors: list[ColorInfo] = field(default_factory=list)
    typography: list[TypographyInfo] = field(default_factory=list)
    spacing: list[SpacingInfo] = field(default_factory=list)
    border_radius: list[int] = field(default_factory=list)
    shadows: list[str] = field(default_factory=list)
    score: float = 0.0  # 0-100 design consistency score
    issues: list[str] = field(default_factory=list)


# Common 4px/8px spacing scales
SPACING_SCALE_4 = [0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 80, 96, 128]
SPACING_SCALE_8 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 128]

# Semantic color role detection thresholds
BRIGHTNESS_THRESHOLD = 0.85  # above = likely background
DARKNESS_THRESHOLD = 0.15  # below = likely text
SATURATION_THRESHOLD = 0.1  # below = likely neutral/border


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return h * 360, s, l


def _classify_color_role(hex_color: str) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    h, s, l = _rgb_to_hsl(r, g, b)

    if l > BRIGHTNESS_THRESHOLD:
        return 'background'
    if l < DARKNESS_THRESHOLD:
        return 'text'
    if s < SATURATION_THRESHOLD:
        return 'border'
    if s > 0.3:
        return 'accent'
    return 'unknown'


def _closest_spacing_scale(value: int) -> int | None:
    best = None
    best_dist = float('inf')
    for i, scale_val in enumerate(SPACING_SCALE_8):
        dist = abs(value - scale_val)
        if dist < best_dist:
            best_dist = dist
            best = i
    if best_dist <= 2:
        return best
    return None


class DesignAnalyzer:
    """Analyzes design patterns from CSS/HTML/screenshot data."""

    async def analyze_css(self, css_content: str) -> DesignReport:
        """Analyze CSS content for design patterns."""
        report = DesignReport()
        report.colors = self._extract_colors(css_content)
        report.typography = self._extract_typography(css_content)
        report.spacing = self._extract_spacing(css_content)
        report.border_radius = self._extract_border_radius(css_content)
        report.shadows = self._extract_shadows(css_content)
        report.score = self._calculate_score(report)
        report.issues = self._find_issues(report)
        return report

    async def analyze_screenshot(self, image_path: Path) -> DesignReport:
        """Analyze a screenshot for design patterns.

        Requires PIL/Pillow for image analysis.
        """
        try:
            from PIL import Image
        except ImportError:
            logger.warning('Pillow not installed — screenshot analysis unavailable')
            return DesignReport()

        if not image_path.exists():
            logger.error('Screenshot not found: %s', image_path)
            return DesignReport()

        img = Image.open(image_path).convert('RGB')
        report = DesignReport()
        report.colors = self._extract_colors_from_image(img)
        report.score = self._calculate_score(report)
        report.issues = self._find_issues(report)
        return report

    def _extract_colors(self, css: str) -> list[ColorInfo]:
        """Extract color values from CSS."""
        import re

        hex_pattern = r'#([0-9a-fA-F]{6})\b'
        rgb_pattern = r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)'
        rgba_pattern = r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)'

        color_counts: Counter[str] = Counter()

        for match in re.finditer(hex_pattern, css):
            color_counts[f'#{match.group(1).lower()}'] += 1

        for match in re.finditer(rgb_pattern, css):
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            color_counts[f'#{r:02x}{g:02x}{b:02x}'] += 1

        for match in re.finditer(rgba_pattern, css):
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            color_counts[f'#{r:02x}{g:02x}{b:02x}'] += 1

        total = sum(color_counts.values()) or 1
        results = []
        for color, count in color_counts.most_common(20):
            r, g, b = _hex_to_rgb(color)
            results.append(
                ColorInfo(
                    hex=color,
                    rgb=(r, g, b),
                    count=count,
                    percentage=round(count / total * 100, 1),
                    role=_classify_color_role(color),
                )
            )
        return results

    def _extract_colors_from_image(self, img: Any) -> list[ColorInfo]:
        """Extract dominant colors from an image using quantization."""
        try:
            from PIL import Image
        except ImportError:
            return []

        # Resize for speed
        small = img.copy()
        small.thumbnail((150, 150))
        quantized = small.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()

        if not palette:
            return []

        color_counts: Counter[str] = Counter()
        pixels = list(quantized.getdata())
        for pixel_idx in pixels:
            idx = pixel_idx * 3
            r, g, b = palette[idx], palette[idx + 1], palette[idx + 2]
            color_counts[f'#{r:02x}{g:02x}{b:02x}'] += 1

        total = sum(color_counts.values()) or 1
        results = []
        for color, count in color_counts.most_common(12):
            r, g, b = _hex_to_rgb(color)
            results.append(
                ColorInfo(
                    hex=color,
                    rgb=(r, g, b),
                    count=count,
                    percentage=round(count / total * 100, 1),
                    role=_classify_color_role(color),
                )
            )
        return results

    def _extract_typography(self, css: str) -> list[TypographyInfo]:
        """Extract typography patterns from CSS."""
        import re

        font_pattern = r'font-family:\s*([^;]+);'
        size_pattern = r'font-size:\s*(\d+)px'
        weight_pattern = r'font-weight:\s*(\d+)'

        families = re.findall(font_pattern, css, re.IGNORECASE)
        sizes = [int(s) for s in re.findall(size_pattern, css, re.IGNORECASE)]

        results = []
        size_counts = Counter(sizes)
        for size, count in size_counts.most_common(10):
            results.append(
                TypographyInfo(
                    font_family=families[0] if families else 'unknown',
                    font_size=size,
                    font_weight=400,
                    count=count,
                )
            )
        return results

    def _extract_spacing(self, css: str) -> list[SpacingInfo]:
        """Extract spacing values from CSS."""
        import re

        spacing_pattern = r'(?:padding|margin|gap):\s*(\d+)px'
        values = [int(v) for v in re.findall(spacing_pattern, css, re.IGNORECASE)]

        value_counts = Counter(values)
        results = []
        for value, freq in value_counts.most_common(15):
            results.append(
                SpacingInfo(
                    value=value,
                    frequency=freq,
                    scale_position=_closest_spacing_scale(value),
                )
            )
        return results

    def _extract_border_radius(self, css: str) -> list[int]:
        """Extract border-radius values."""
        import re

        pattern = r'border-radius:\s*(\d+)px'
        values = [int(v) for v in re.findall(pattern, css, re.IGNORECASE)]
        return sorted(set(values))

    def _extract_shadows(self, css: str) -> list[str]:
        """Extract box-shadow values."""
        import re

        pattern = r'box-shadow:\s*([^;]+);'
        return list(set(re.findall(pattern, css, re.IGNORECASE)))

    def _calculate_score(self, report: DesignReport) -> float:
        """Calculate design consistency score (0-100)."""
        score = 100.0

        # Penalize too many colors
        if len(report.colors) > 10:
            score -= (len(report.colors) - 10) * 2

        # Penalize inconsistent spacing (values not on 4px grid)
        off_grid = sum(1 for s in report.spacing if s.scale_position is None)
        if report.spacing:
            score -= (off_grid / len(report.spacing)) * 20

        # Penalize too many font sizes
        if len(report.typography) > 6:
            score -= (len(report.typography) - 6) * 3

        # Penalize too many border radius values
        if len(report.border_radius) > 4:
            score -= (len(report.border_radius) - 4) * 5

        return max(0.0, min(100.0, score))

    def _find_issues(self, report: DesignReport) -> list[str]:
        """Identify design consistency issues."""
        issues = []

        if len(report.colors) > 10:
            issues.append(
                f'Too many colors ({len(report.colors)}). Consider reducing to 8-10.'
            )

        off_grid = [s for s in report.spacing if s.scale_position is None]
        if off_grid:
            values = [str(s.value) for s in off_grid[:5]]
            issues.append(f'Spacing values not on 8px grid: {", ".join(values)}')

        if len(report.typography) > 6:
            issues.append(
                f'Too many font sizes ({len(report.typography)}). Consider a type scale.'
            )

        if len(report.border_radius) > 4:
            issues.append(
                f'Too many border-radius values ({len(report.border_radius)}). Standardize.'
            )

        # Check for accent colors with low usage (might be orphaned)
        accents = [c for c in report.colors if c.role == 'accent']
        low_use = [c for c in accents if c.percentage < 1.0]
        if low_use:
            issues.append(
                f'{len(low_use)} accent color(s) used <1% of the time. Consider removing.'
            )

        return issues
