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


def extract_tax_unit_data(year: int = 2026) -> dict[str, np.ndarray]:
    """Run the baseline US microsimulation and return per-tax-unit arrays.

    Parameters
    ----------
    year : int
        Calendar year for the simulation.

    Returns
    -------
    dict
        AGI, federal income tax, employee payroll tax, and weight for every
        tax unit, as numpy arrays.
    """
    _require_policyengine_us()
    from policyengine_us import Microsimulation  # type: ignore[import-not-found]

    sim = Microsimulation()
    agi = sim.calc("adjusted_gross_income", period=year)
    income_tax = sim.calc("income_tax", period=year)
    payroll_tax = sim.calc("employee_payroll_tax", period=year)
    weight = sim.calc("tax_unit_weight", period=year)
    return {
        "agi": np.asarray(agi, dtype=float),
        "income_tax": np.asarray(income_tax, dtype=float),
        "payroll_tax": np.asarray(payroll_tax, dtype=float),
        "weight": np.asarray(weight, dtype=float),
    }
