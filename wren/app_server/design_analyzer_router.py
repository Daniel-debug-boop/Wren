"""Design Analyzer API route.

POST /api/v1/design-analyze — Analyze CSS content for design patterns.
POST /api/v1/design-analyze/screenshot — Analyze a screenshot for design patterns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from wren.app_server.design_analyzer import DesignAnalyzer

router = APIRouter(prefix='/api/v1/design-analyze', tags=['design-analyzer'])

analyzer = DesignAnalyzer()


class AnalyzeCssRequest(BaseModel):
    css: str = Field(description='CSS content to analyze')


class AnalyzeCssResponse(BaseModel):
    colors: list[dict[str, Any]]
    typography: list[dict[str, Any]]
    spacing: list[dict[str, Any]]
    border_radius: list[int]
    shadows: list[str]
    score: float
    issues: list[str]


@router.post('', response_model=AnalyzeCssResponse)
async def analyze_css(request: AnalyzeCssRequest) -> AnalyzeCssResponse:
    """Analyze CSS content for design patterns (colors, typography, spacing, etc.)."""
    if not request.css.strip():
        raise HTTPException(status_code=400, detail='CSS content cannot be empty')

    report = await analyzer.analyze_css(request.css)

    return AnalyzeCssResponse(
        colors=[
            {
                'hex': c.hex,
                'rgb': list(c.rgb),
                'count': c.count,
                'percentage': c.percentage,
                'role': c.role,
            }
            for c in report.colors
        ],
        typography=[
            {
                'font_family': t.font_family,
                'font_size': t.font_size,
                'font_weight': t.font_weight,
                'count': t.count,
            }
            for t in report.typography
        ],
        spacing=[
            {
                'value': s.value,
                'frequency': s.frequency,
                'scale_position': s.scale_position,
            }
            for s in report.spacing
        ],
        border_radius=report.border_radius,
        shadows=report.shadows,
        score=report.score,
        issues=report.issues,
    )


@router.post('/screenshot', response_model=AnalyzeCssResponse)
async def analyze_screenshot(file: UploadFile = File(...)) -> AnalyzeCssResponse:
    """Analyze a screenshot image for design patterns (dominant colors, etc.)."""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='File must be an image')

    try:
        from PIL import Image
        import io
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail='Pillow not installed. Run: pip install pillow',
        )

    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Invalid image: {e}')

    import tempfile, os

    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp_path = Path(tmp.name)
        report = await analyzer.analyze_screenshot(tmp_path)
    finally:
        if tmp and os.path.exists(tmp.name):
            os.unlink(tmp.name)

    return AnalyzeCssResponse(
        colors=[
            {
                'hex': c.hex,
                'rgb': list(c.rgb),
                'count': c.count,
                'percentage': c.percentage,
                'role': c.role,
            }
            for c in report.colors
        ],
        typography=[],
        spacing=[],
        border_radius=[],
        shadows=[],
        score=report.score,
        issues=report.issues,
    )
