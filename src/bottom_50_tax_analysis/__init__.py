"""Federal income tax burden by income percentile.

This package supports the interactive analysis at
https://github.com/PolicyEngine/bottom-50-tax-analysis.
"""

from __future__ import annotations

__version__ = "0.1.0"

from . import fallback, reforms, shares

__all__ = ["__version__", "fallback", "reforms", "shares"]
