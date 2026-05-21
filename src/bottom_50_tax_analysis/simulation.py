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


DATASETS = {
    "cps_2024": "hf://policyengine/policyengine-us-data/cps_2024.h5",
    "enhanced_cps_2024": "hf://policyengine/policyengine-us-data/enhanced_cps_2024.h5",
    "pooled_3_year_cps_2023": "hf://policyengine/policyengine-us-data/pooled_3_year_cps_2023.h5",
}

# Default dataset for SOI comparison: plain Census CPS uprated by PolicyEngine.
# It produces total federal income tax within 1% of IRS SOI's published
# tabulation, because its underlying data is Form-1040-equivalent.
# The Enhanced CPS adds synthetic high-net-worth tax units calibrated to
# Saez/Zucman top-income shares — useful for distributional analysis at the
# top, but produces total tax ~2.4× SOI which is not what we want for an
# IRS replication.
DEFAULT_DATASET = "cps_2024"


def extract_tax_unit_data(
    year: int = 2026,
    *,
    filers_only: bool = True,
    dataset: str = DEFAULT_DATASET,
) -> dict[str, np.ndarray]:
    """Run the baseline US microsimulation and return per-tax-unit arrays.

    Parameters
    ----------
    year : int
        Calendar year for the simulation.
    filers_only : bool, default True
        If True, drop tax units where ``tax_unit_is_filer`` is False so the
        population matches IRS SOI (which only tabulates filed returns).
    dataset : str, default "cps_2024"
        Which PolicyEngine-US dataset to use. ``cps_2024`` is the plain
        Census CPS uprated by PE; it matches IRS SOI totals to within 1%
        but understates the very top of the income distribution because
        CPS is top-coded. ``enhanced_cps_2024`` (PE's standard) adds
        synthetic high-net-worth tax units calibrated to Saez/Zucman
        top-income shares — total federal income tax comes out ~2.4× IRS
        SOI, which is intentional in PE's design but is not an apples-
        to-apples match for SOI tabulations.

    Returns
    -------
    dict
        AGI, federal income tax, employee payroll tax, weight, and
        population-scope metadata as numpy arrays.
    """
    _require_policyengine_us()
    from policyengine_us import Microsimulation  # type: ignore[import-not-found]

    if dataset not in DATASETS:
        raise ValueError(f"Unknown dataset {dataset!r}. Choices: {sorted(DATASETS)}.")
    sim = Microsimulation(dataset=DATASETS[dataset])
    agi = np.asarray(sim.calc("adjusted_gross_income", period=year), dtype=float)
    # ``income_tax`` is net of refundable credits — PE's standard measure,
    # what you'd use for a budget score. Can be negative for refund recipients.
    income_tax_net = np.asarray(sim.calc("income_tax", period=year), dtype=float)
    # ``income_tax_before_refundable_credits`` is the apples-to-apples match
    # for the IRS SOI "Total Income Tax" line that Tax Foundation
    # distributes by AGI percentile: regular tax + AMT + NIIT + other
    # surtaxes, after non-refundable credits, before refundable credits.
    income_tax_gross = np.asarray(
        sim.calc("income_tax_before_refundable_credits", period=year),
        dtype=float,
    )
    payroll_tax = np.asarray(sim.calc("employee_payroll_tax", period=year), dtype=float)
    weight = np.asarray(sim.calc("tax_unit_weight", period=year), dtype=float)
    is_filer = np.asarray(sim.calc("tax_unit_is_filer", period=year), dtype=bool)

    if filers_only:
        mask = is_filer
    else:
        mask = np.ones_like(is_filer, dtype=bool)

    return {
        "agi": agi[mask],
        "income_tax_gross": income_tax_gross[mask],
        "income_tax_net": income_tax_net[mask],
        "payroll_tax": payroll_tax[mask],
        "weight": weight[mask],
        "population_scope": "filers" if filers_only else "all_tax_units",
        "filer_share": float(weight[is_filer].sum() / weight.sum()),
        "dataset": dataset,
    }
