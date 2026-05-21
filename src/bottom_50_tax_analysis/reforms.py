"""Reform definitions for ``bottom_50_tax_analysis``.

The headline reform is "zero out federal income tax for tax units below the
50th-percentile AGI cutoff." PolicyEngine does not have a built-in parameter
for this — it requires a custom Reform that modifies ``income_tax`` to be
zero when ``adjusted_gross_income < threshold``. ``simulation.py`` builds
that Reform from the dict returned here.
"""

from __future__ import annotations

from typing import Any


def zero_income_tax_below(*, threshold: float, year: int) -> dict[str, Any]:
    """Define the zero-tax-below-threshold reform.

    Returns
    -------
    dict
        A reform descriptor consumed by ``simulation.apply_reform``.
        The dict carries the threshold and target year; the simulation
        wrapper uses these to construct a runtime ``Reform`` object.
    """
    return {
        "name": "zero_income_tax_below_p50",
        "bottom_50_cutoff": float(threshold),
        "year": int(year),
    }


def describe(*, threshold: float, year: int) -> str:
    """Human-readable summary used in the frontend results page."""
    return (
        f"Zero out federal income tax for all tax units with AGI under "
        f"${threshold:,.0f} in {year}."
    )
