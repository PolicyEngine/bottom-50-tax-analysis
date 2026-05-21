"""PolicyEngine-US microsimulation wrapper.

This module is imported lazily — ``policyengine-us`` is heavy and is an
**optional** dependency (``pip install bottom-50-tax-analysis[sim]``).
Calling :func:`extract_tax_unit_data` raises a helpful ImportError if the
package is missing.

The wrapper extracts AGI, federal income tax, and (employee-side) payroll
tax for every tax unit, with the household weight mapped to the tax_unit
level so the percentile-share math in :mod:`shares` can use the weights
directly. For the "zero income tax below the 50th-percentile cutoff" reform
we use a static estimate (see :func:`shares.revenue_cost_of_zeroing_below`):
because the reform just forces ``income_tax = 0`` for the affected tax
units, the revenue cost is identical to the weighted sum of their
baseline ``income_tax``. Behavioural and state-tax interactions are not
modelled.
"""

from __future__ import annotations

import numpy as np


def _require_policyengine_us() -> None:
    try:
        import policyengine_us  # noqa: F401
    except ImportError as exc:  # pragma: no cover — exercised only without [sim]
        raise ImportError(
            "policyengine-us is not installed. Install with:\n"
            "    uv pip install '.[sim]'\n"
            "or use the fallback path (``bottom50-generate`` without "
            "``--live``)."
        ) from exc


def extract_tax_unit_data(
    year: int = 2026, *, filers_only: bool = True
) -> dict[str, np.ndarray]:
    """Run the baseline US microsimulation and return per-tax-unit arrays.

    Parameters
    ----------
    year : int
        Calendar year for the simulation.
    filers_only : bool, default True
        If True, drop tax units where ``tax_unit_is_filer`` is False so the
        population matches IRS SOI (which only tabulates filed returns).
        Non-filer tax units in the Enhanced CPS otherwise pull the median
        AGI down and depress the bottom-50 share.

    Returns
    -------
    dict
        AGI, federal income tax, employee payroll tax, weight, and
        population-scope metadata as numpy arrays.
    """
    _require_policyengine_us()
    from policyengine_us import Microsimulation  # type: ignore[import-not-found]

    sim = Microsimulation()
    agi = np.asarray(sim.calc("adjusted_gross_income", period=year), dtype=float)
    income_tax = np.asarray(sim.calc("income_tax", period=year), dtype=float)
    payroll_tax = np.asarray(sim.calc("employee_payroll_tax", period=year), dtype=float)
    weight = np.asarray(sim.calc("tax_unit_weight", period=year), dtype=float)
    is_filer = np.asarray(sim.calc("tax_unit_is_filer", period=year), dtype=bool)

    if filers_only:
        mask = is_filer
    else:
        mask = np.ones_like(is_filer, dtype=bool)

    return {
        "agi": agi[mask],
        "income_tax": income_tax[mask],
        "payroll_tax": payroll_tax[mask],
        "weight": weight[mask],
        "population_scope": "filers" if filers_only else "all_tax_units",
        "filer_share": float(weight[is_filer].sum() / weight.sum()),
    }
