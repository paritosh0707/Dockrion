"""
Template System Module
======================

Provides a robust, flexible template system for generating:
- FastAPI runtime code
- Dockerfiles
- Requirements files
- Other deployment artifacts
"""

from .renderer import (
    TemplateRenderer,
    TemplateContext,
    render_runtime,
    render_dockerfile,
    render_requirements,
    get_renderer,
    DOCKRION_VERSION,
    TEMPLATE_FILES,
)

__all__ = [
    "TemplateRenderer",
    "TemplateContext",
    "render_runtime",
    "render_dockerfile",
    "render_requirements",
    "get_renderer",
    "DOCKRION_VERSION",
    "TEMPLATE_FILES",
]

